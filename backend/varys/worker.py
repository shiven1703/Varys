"""Dedicated worker process entrypoint."""

from __future__ import annotations

import argparse
import logging
import signal
from threading import Event
from types import FrameType
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from varys.config import load_settings
from varys.db import create_session_factory
from varys.logging import configure_logging
from varys.packages import reconcile_packages
from varys.runs import (
    Run,
    RunState,
    apply_requested_action_at_checkpoint,
    claim_next_run,
    finish_run_at_checkpoint,
    heartbeat,
    recover_expired_leases,
)
from varys.storage import StoragePaths, initialize_storage
from varys.workflows import WorkflowError, execute_daily_fixture_run

_LOGGER = logging.getLogger("varys.worker")
_POLL_INTERVAL_SECONDS = 1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    settings = load_settings()
    configure_logging(settings.log_level, service="worker")
    factory: sessionmaker[Session] | None = None
    paths = StoragePaths.from_root(settings.data_root) if settings.data_root else None
    if paths is not None:
        initialize_storage(paths)
    if settings.database_url is not None:
        factory = create_session_factory(settings.database_url)
        _process_once(factory, paths, settings.worker_id)
    _LOGGER.info(
        "worker bootstrap complete",
        extra={"service": "worker", "worker_id": settings.worker_id},
    )
    if arguments.check:
        return 0
    _wait_for_shutdown(factory, paths, settings.worker_id)
    return 0


def _process_once(
    factory: sessionmaker[Session], paths: StoragePaths | None, worker_id: str
) -> None:
    try:
        with factory.begin() as database:
            recovered = recover_expired_leases(database)
            reconciliation = reconcile_packages(database, paths) if paths else None
            claimed = claim_next_run(database, worker_id)
            run_id = claimed.id if claimed else None
    except SQLAlchemyError:
        _LOGGER.warning(
            "worker database is not ready; retrying",
            extra={"service": "worker"},
        )
        return
    if (
        run_id is not None
        or recovered
        or (
            reconciliation
            and (
                reconciliation.adopted
                or reconciliation.quarantined
                or reconciliation.staged_parts
            )
        )
    ):
        _LOGGER.info(
            "worker dispatch reconciliation complete",
            extra={
                "service": "worker",
                "recovered_runs": recovered,
                "claimed_run_id": str(run_id) if run_id else None,
                "adopted_packages": reconciliation.adopted if reconciliation else 0,
                "quarantined_packages": (
                    reconciliation.quarantined if reconciliation else 0
                ),
                "staged_package_parts": (
                    reconciliation.staged_parts if reconciliation else 0
                ),
            },
        )
    if run_id is not None and paths is not None:
        _execute_claimed_run(factory, paths, run_id, worker_id)


def _execute_claimed_run(
    factory: sessionmaker[Session], paths: StoragePaths, run_id: UUID, worker_id: str
) -> None:
    with factory.begin() as database:
        run = database.get(Run, run_id)
        if run is None or apply_requested_action_at_checkpoint(
            database, run, worker_id
        ):
            return
        if not heartbeat(database, run, worker_id):
            return
        try:
            published = execute_daily_fixture_run(database, paths, run)
        except (OSError, ValueError, WorkflowError):
            _LOGGER.exception(
                "fixture run failed",
                extra={"service": "worker", "run_id": str(run.id)},
            )
            finish_run_at_checkpoint(database, run, worker_id, RunState.FAILED)
            return
        finish_run_at_checkpoint(
            database,
            run,
            worker_id,
            RunState.COMPLETED if published else RunState.COMPLETED_WITH_WARNINGS,
        )


def _wait_for_shutdown(
    factory: sessionmaker[Session] | None, paths: StoragePaths | None, worker_id: str
) -> None:
    shutdown = Event()

    def request_shutdown(_signal_number: int, _frame: FrameType | None) -> None:
        shutdown.set()

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)
    while not shutdown.wait(_POLL_INTERVAL_SECONDS):
        if factory is not None:
            _process_once(factory, paths, worker_id)


if __name__ == "__main__":
    raise SystemExit(main())
