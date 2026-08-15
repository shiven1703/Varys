import os

import pytest

from varys.auth import AuthSession, create_user, current_user, login, revoke_session
from varys.db import check_database_readiness, create_session_factory, upgrade_database


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
