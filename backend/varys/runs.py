"""PostgreSQL-backed run state, claiming, leases, and events."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from varys.auth import Base

LEASE_DURATION = timedelta(minutes=5)
_DISPATCH_LOCK_ID = 904_312_640


class RunState(StrEnum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_FOR_SOURCE = "WAITING_FOR_SOURCE"
    PAUSED = "PAUSED"
    SOURCE_BLOCKED = "SOURCE_BLOCKED"
    COMPLETED = "COMPLETED"
    COMPLETED_WITH_WARNINGS = "COMPLETED_WITH_WARNINGS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class RequestedAction(StrEnum):
    PAUSE = "PAUSE"
    CANCEL = "CANCEL"


ACTIVE_RUN_STATES = (
    RunState.RUNNING,
    RunState.WAITING_FOR_SOURCE,
    RunState.PAUSED,
    RunState.SOURCE_BLOCKED,
)
TERMINAL_RUN_STATES = (
    RunState.COMPLETED,
    RunState.COMPLETED_WITH_WARNINGS,
    RunState.FAILED,
    RunState.CANCELLED,
)


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    kind: Mapped[str] = mapped_column(String(32))
    state: Mapped[str] = mapped_column(String(32), default=RunState.QUEUED)
    worker_id: Mapped[str | None] = mapped_column(String(128))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    requested_action: Mapped[str | None] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class RunEvent(Base):
    __tablename__ = "run_events"

    id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid4
    )
    run_id: Mapped[UUID] = mapped_column(ForeignKey("runs.id"), index=True)
    sequence: Mapped[int] = mapped_column()
    event_type: Mapped[str] = mapped_column(String(64))
    from_state: Mapped[str | None] = mapped_column(String(32))
    to_state: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def claim_next_run(database: Session, worker_id: str) -> Run | None:
    database.execute(select(func.pg_advisory_xact_lock(_DISPATCH_LOCK_ID)))
    active_run = database.scalar(
        select(Run).where(Run.state.in_(ACTIVE_RUN_STATES)).with_for_update().limit(1)
    )
    if active_run is not None:
        return None
    run = database.scalar(
        select(Run)
        .where(Run.state == RunState.QUEUED)
        .order_by(Run.created_at, Run.id)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if run is None:
        return None
    _transition(database, run, RunState.RUNNING, "CLAIMED")
    now = _now()
    run.worker_id = worker_id
    run.heartbeat_at = now
    run.lease_expires_at = now + LEASE_DURATION
    return run


def heartbeat(database: Session, run: Run, worker_id: str) -> bool:
    if run.state != RunState.RUNNING or run.worker_id != worker_id:
        return False
    now = _now()
    if run.lease_expires_at is None or now >= run.lease_expires_at:
        return False
    run.heartbeat_at = now
    run.lease_expires_at = now + LEASE_DURATION
    run.updated_at = now
    return True


def recover_expired_leases(database: Session) -> int:
    now = _now()
    runs = database.scalars(
        select(Run)
        .where(
            Run.state == RunState.RUNNING,
            Run.lease_expires_at.is_not(None),
            Run.lease_expires_at <= now,
        )
        .with_for_update(skip_locked=True)
    )
    count = 0
    for run in runs:
        _transition(database, run, RunState.QUEUED, "LEASE_EXPIRED")
        run.worker_id = None
        run.lease_expires_at = None
        run.heartbeat_at = None
        count += 1
    return count


def create_run(database: Session, kind: str) -> Run:
    normalized_kind = kind.strip()
    if not normalized_kind:
        raise ValueError("run kind is required")
    now = _now()
    run = Run(
        kind=normalized_kind,
        state=RunState.QUEUED,
        worker_id=None,
        lease_expires_at=None,
        heartbeat_at=None,
        requested_action=None,
        created_at=now,
        updated_at=now,
    )
    database.add(run)
    database.flush()
    _append_event(database, run, "CREATED", None, RunState.QUEUED)
    return run


def request_action(database: Session, run: Run, action: RequestedAction) -> bool:
    if action not in (RequestedAction.PAUSE, RequestedAction.CANCEL):
        raise ValueError("unsupported requested action")
    if run.state != RunState.RUNNING or run.requested_action is not None:
        return False
    run.requested_action = action
    run.updated_at = _now()
    _append_event(database, run, f"{action}_REQUESTED", run.state, run.state)
    return True


def apply_requested_action_at_checkpoint(
    database: Session, run: Run, worker_id: str
) -> RunState | None:
    if run.state != RunState.RUNNING or run.worker_id != worker_id:
        return None
    action = run.requested_action
    if action is None:
        return None
    if action == RequestedAction.PAUSE:
        target_state = RunState.PAUSED
    elif action == RequestedAction.CANCEL:
        target_state = RunState.CANCELLED
    else:
        raise ValueError("unsupported requested action")
    _transition(database, run, target_state, f"{action}_APPLIED")
    _clear_worker_lease(run)
    run.requested_action = None
    return target_state


def resume_paused_run(database: Session, run: Run) -> bool:
    if run.state != RunState.PAUSED:
        return False
    _transition(database, run, RunState.QUEUED, "RESUMED")
    _clear_worker_lease(run)
    return True


def finish_run_at_checkpoint(
    database: Session, run: Run, worker_id: str, state: RunState
) -> bool:
    if (
        run.state != RunState.RUNNING
        or run.worker_id != worker_id
        or state not in TERMINAL_RUN_STATES
        or run.requested_action is not None
    ):
        return False
    _transition(database, run, state, state)
    _clear_worker_lease(run)
    return True


def _transition(database: Session, run: Run, state: RunState, event_type: str) -> None:
    previous_state = run.state
    _append_event(database, run, event_type, previous_state, state)
    run.state = state
    run.updated_at = _now()


def _append_event(
    database: Session,
    run: Run,
    event_type: str,
    from_state: str | None,
    to_state: str | None,
) -> None:
    last_sequence = database.scalar(
        select(RunEvent.sequence)
        .where(RunEvent.run_id == run.id)
        .order_by(RunEvent.sequence.desc())
        .limit(1)
    )
    database.add(
        RunEvent(
            run_id=run.id,
            sequence=(last_sequence or 0) + 1,
            event_type=event_type,
            from_state=from_state,
            to_state=to_state,
            created_at=_now(),
        )
    )


def _clear_worker_lease(run: Run) -> None:
    run.worker_id = None
    run.lease_expires_at = None
    run.heartbeat_at = None


def _now() -> datetime:
    return datetime.now(UTC)
