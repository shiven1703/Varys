from unittest.mock import MagicMock, patch

from sqlalchemy.exc import OperationalError

from varys.db import DatabaseReadiness, check_database_readiness, create_database_engine


def test_readiness_fails_without_database_url() -> None:
    assert check_database_readiness(None) == DatabaseReadiness(
        False, "database URL is not configured"
    )


def test_readiness_fails_when_postgresql_is_unreachable() -> None:
    connection_error = OperationalError("", {}, RuntimeError())
    unavailable_engine = patch(
        "varys.db.create_database_engine", side_effect=connection_error
    )
    with unavailable_engine:
        readiness = check_database_readiness("postgresql://localhost/varys")

    assert readiness.ready is False
    assert readiness.reason == "database is unavailable: OperationalError"


def test_non_postgresql_urls_are_rejected() -> None:
    try:
        create_database_engine("sqlite://")
    except ValueError as error:
        assert str(error) == "VARYS_DATABASE_URL must use PostgreSQL"
    else:
        raise AssertionError("SQLite URL was accepted")


def test_readiness_fails_when_database_revision_is_not_at_head() -> None:
    engine = MagicMock()
    with (
        patch("varys.db.create_database_engine", return_value=engine),
        patch("varys.db.get_database_revision", return_value="old-revision"),
        patch("varys.db.migration_head_revision", return_value="head-revision"),
    ):
        readiness = check_database_readiness("postgresql://localhost/varys")

    assert readiness == DatabaseReadiness(
        False, "database migration revision is incompatible"
    )
