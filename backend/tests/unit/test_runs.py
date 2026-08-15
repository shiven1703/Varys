from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from varys.runs import (
    RequestedAction,
    Run,
    RunState,
    apply_requested_action_at_checkpoint,
    finish_run_at_checkpoint,
    heartbeat,
    request_action,
    resume_paused_run,
)


def test_pause_and_cancel_are_applied_only_at_worker_checkpoints() -> None:
    database = MagicMock()
    database.scalar.return_value = None
    run = _running_run()

    assert request_action(database, run, RequestedAction.PAUSE) is True
    assert run.state == RunState.RUNNING
    assert (
        apply_requested_action_at_checkpoint(database, run, "worker-1")
        == RunState.PAUSED
    )
    assert run.worker_id is None
    assert resume_paused_run(database, run) is True
    run.state = RunState.RUNNING
    run.worker_id = "worker-1"
    run.heartbeat_at = datetime.now(UTC)
    run.lease_expires_at = datetime.now(UTC) + timedelta(minutes=5)

    assert request_action(database, run, RequestedAction.CANCEL) is True
    assert (
        finish_run_at_checkpoint(database, run, "worker-1", RunState.COMPLETED) is False
    )
    assert (
        apply_requested_action_at_checkpoint(database, run, "worker-1")
        == RunState.CANCELLED
    )


def test_heartbeat_rejects_wrong_worker_and_expired_lease() -> None:
    database = MagicMock()
    run = _running_run()

    assert heartbeat(database, run, "worker-2") is False
    run.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert heartbeat(database, run, "worker-1") is False


def _running_run() -> Run:
    now = datetime.now(UTC)
    return Run(
        id=uuid4(),
        kind="daily",
        state=RunState.RUNNING,
        worker_id="worker-1",
        lease_expires_at=now + timedelta(minutes=5),
        heartbeat_at=now,
        requested_action=None,
        created_at=now,
        updated_at=now,
    )
