"""PostgreSQL sessions, migration checks, and readiness support."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import cast

from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, Engine, create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker


@dataclass(frozen=True, slots=True)
class DatabaseReadiness:
    ready: bool
    reason: str | None = None


def create_database_engine(database_url: str) -> Engine:
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise ValueError("VARYS_DATABASE_URL must use PostgreSQL")
    normalized_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(normalized_url, pool_pre_ping=True)


def create_session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(create_database_engine(database_url), expire_on_commit=False)


def check_database_readiness(database_url: str | None) -> DatabaseReadiness:
    if database_url is None:
        return DatabaseReadiness(False, "database URL is not configured")

    try:
        engine = create_database_engine(database_url)
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            current_revision = get_database_revision(connection)
        engine.dispose()
    except (SQLAlchemyError, ValueError) as error:
        return DatabaseReadiness(
            False, f"database is unavailable: {error.__class__.__name__}"
        )

    head_revision = migration_head_revision()
    if current_revision != head_revision:
        return DatabaseReadiness(False, "database migration revision is incompatible")
    return DatabaseReadiness(True)


def get_database_revision(connection: Connection) -> str | None:
    try:
        statement = text("SELECT version_num FROM alembic_version")
        return cast(str, connection.execute(statement).scalar_one())
    except SQLAlchemyError:
        return None


def migration_head_revision() -> str:
    script = ScriptDirectory.from_config(_alembic_config())
    head_revision = script.get_current_head()
    if head_revision is None:
        raise RuntimeError("Alembic head revision is not configured")
    return head_revision


def upgrade_database(database_url: str) -> None:
    config = _alembic_config()
    config.set_main_option("sqlalchemy.url", _postgresql_url(database_url))
    command.upgrade(config, "head")


def _alembic_config() -> Config:
    repository_root = Path(__file__).resolve().parents[2]
    return Config(str(repository_root / "alembic.ini"))


def _postgresql_url(database_url: str) -> str:
    if not database_url.startswith(("postgresql://", "postgresql+psycopg://")):
        raise ValueError("VARYS_DATABASE_URL must use PostgreSQL")
    return database_url.replace("postgresql://", "postgresql+psycopg://", 1)
