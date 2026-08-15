"""Dedicated worker process entrypoint."""

from __future__ import annotations

import argparse
import logging
import signal
from threading import Event
from types import FrameType

from varys.config import load_settings
from varys.db import create_session_factory
from varys.logging import configure_logging
from varys.runs import claim_next_run, recover_expired_leases

_LOGGER = logging.getLogger("varys.worker")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    settings = load_settings()
    configure_logging(settings.log_level, service="worker")
    if settings.database_url is not None:
        factory = create_session_factory(settings.database_url)
        with factory.begin() as database:
            recovered = recover_expired_leases(database)
            claimed = claim_next_run(database, settings.worker_id)
        _LOGGER.info(
            "worker dispatch reconciliation complete",
            extra={
                "service": "worker",
                "recovered_runs": recovered,
                "claimed_run_id": str(claimed.id) if claimed else None,
            },
        )
    _LOGGER.info(
        "worker bootstrap complete",
        extra={"service": "worker", "worker_id": settings.worker_id},
    )
    if arguments.check:
        return 0
    _wait_for_shutdown()
    return 0


def _wait_for_shutdown() -> None:
    shutdown = Event()

    def request_shutdown(_signal_number: int, _frame: FrameType | None) -> None:
        shutdown.set()

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)
    shutdown.wait()


if __name__ == "__main__":
    raise SystemExit(main())
