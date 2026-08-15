import os
from datetime import UTC, datetime, timedelta
from threading import Barrier, Thread

import pytest
from sqlalchemy import delete, update
from sqlalchemy.exc import DBAPIError

from varys.auth import AuthSession, create_user, current_user, login, revoke_session
from varys.db import check_database_readiness, create_session_factory, upgrade_database
from varys.runs import (
    RequestedAction,
    Run,
    RunEvent,
    RunState,
    apply_requested_action_at_checkpoint,
    claim_next_run,
    create_run,
    recover_expired_leases,
    request_action,
    resume_paused_run,
)


@pytest.mark.integration
def test_clean_postgresql_database_migrates_to_head() -> None:
    database_url = os.getenv("VARYS_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("VARYS_TEST_DATABASE_URL is not configured")
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        pytest.fail("VARYS_TEST_DATABASE_URL must use PostgreSQL")

    upgrade_database(database_url)

    assert check_database_readiness(database_url).ready is True


@pytest.mark.integration
def test_authentication_sessions_are_revocable_and_server_side() -> None:
    database_url = os.getenv("VARYS_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("VARYS_TEST_DATABASE_URL is not configured")
    upgrade_database(database_url)
    factory = create_session_factory(database_url)
    username = f"admin-{os.urandom(8).hex()}"
    with factory.begin() as database:
        user = create_user(database, username, "correct horse battery staple")
    with factory.begin() as database:
        authenticated = login(
            database, username, "correct horse battery staple", "test-session-secret"
        )
        assert authenticated is not None
        _user, session_token, csrf_token = authenticated
    with factory.begin() as database:
        assert current_user(database, session_token, "test-session-secret") is not None
        stored_session = database.query(AuthSession).filter_by(user_id=user.id).one()
        assert session_token not in stored_session.token_hash
        assert revoke_session(
            database, session_token, csrf_token, "test-session-secret"
        )
    with factory.begin() as database:
        assert current_user(database, session_token, "test-session-secret") is None


@pytest.mark.integration
def test_run_dispatch_enforces_claims_leases_events_and_safe_controls() -> None:
    database_url = os.getenv("VARYS_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("VARYS_TEST_DATABASE_URL is not configured")
    upgrade_database(database_url)
    factory = create_session_factory(database_url)

    with factory.begin() as database:
        first = create_run(database, "daily")
        second = create_run(database, "daily")
        first_id, second_id = first.id, second.id
    with factory.begin() as database:
        claimed = claim_next_run(database, "worker-1")
        assert claimed is not None and claimed.id == first_id
        assert claim_next_run(database, "worker-2") is None
        assert request_action(database, claimed, RequestedAction.PAUSE) is True
        assert claimed.state == RunState.RUNNING
        assert (
            apply_requested_action_at_checkpoint(database, claimed, "worker-1")
            == RunState.PAUSED
        )
        assert resume_paused_run(database, claimed) is True
    with factory.begin() as database:
        resumed = claim_next_run(database, "worker-2")
        assert resumed is not None and resumed.id == first_id
        assert request_action(database, resumed, RequestedAction.CANCEL) is True
        assert (
            apply_requested_action_at_checkpoint(database, resumed, "worker-2")
            == RunState.CANCELLED
        )
        assert claim_next_run(database, "worker-3") is not None
    with factory.begin() as database:
        active_second = database.get(Run, second_id)
        assert active_second is not None and active_second.state == RunState.RUNNING
        active_second.lease_expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with factory.begin() as database:
        assert recover_expired_leases(database) == 1
        recovered = claim_next_run(database, "worker-4")
        assert recovered is not None and recovered.id == second_id
        assert request_action(database, recovered, RequestedAction.CANCEL) is True
        assert (
            apply_requested_action_at_checkpoint(database, recovered, "worker-4")
            == RunState.CANCELLED
        )
        events = database.query(RunEvent).filter_by(run_id=first_id).all()
        assert [event.sequence for event in events] == list(range(1, len(events) + 1))

    with factory() as database:
        event_id = database.query(RunEvent.id).filter_by(run_id=first_id).first()
        assert event_id is not None
        with pytest.raises(DBAPIError):
            database.execute(
                update(RunEvent)
                .where(RunEvent.id == event_id[0])
                .values(event_type="ALTERED")
            )
            database.commit()
        database.rollback()
        with pytest.raises(DBAPIError):
            database.execute(delete(RunEvent).where(RunEvent.id == event_id[0]))
            database.commit()
        database.rollback()


@pytest.mark.integration
def test_concurrent_workers_claim_only_one_active_run() -> None:
    database_url = os.getenv("VARYS_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("VARYS_TEST_DATABASE_URL is not configured")
    upgrade_database(database_url)
    factory = create_session_factory(database_url)
    with factory.begin() as database:
        create_run(database, "daily")
        create_run(database, "daily")

    barrier = Barrier(2)
    claims: list[tuple[str, str]] = []
    errors: list[Exception] = []

    def claim(worker_id: str) -> None:
        try:
            with factory.begin() as database:
                barrier.wait()
                run = claim_next_run(database, worker_id)
                if run is not None:
                    claims.append((str(run.id), worker_id))
        except Exception as error:
            errors.append(error)

    workers = [Thread(target=claim, args=(f"worker-{number}",)) for number in (1, 2)]
    for worker in workers:
        worker.start()
    for worker in workers:
        worker.join()

    assert errors == []
    assert len(claims) == 1
    with factory.begin() as database:
        run = database.get(Run, claims[0][0])
        assert run is not None
        assert request_action(database, run, RequestedAction.CANCEL) is True
        assert (
            apply_requested_action_at_checkpoint(database, run, claims[0][1])
            == RunState.CANCELLED
        )
