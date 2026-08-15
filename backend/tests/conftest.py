"""Deterministic test defaults."""

from __future__ import annotations

import os
import socket
from collections.abc import Generator

import pytest
from sqlalchemy import text

from varys.db import create_database_engine


@pytest.fixture(autouse=True)
def prohibit_network(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> None:
    if request.node.get_closest_marker("integration") is not None:
        return

    def blocked(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("network access is prohibited in tests")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)


@pytest.fixture(autouse=True)
def isolate_integration_database(
    request: pytest.FixtureRequest,
) -> Generator[None, None, None]:
    yield
    if request.node.get_closest_marker("integration") is None:
        return
    database_url = os.getenv("VARYS_TEST_DATABASE_URL")
    if database_url is None:
        return
    engine = create_database_engine(database_url)
    try:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "TRUNCATE TABLE package_files, packages, run_events, runs, "
                    "auth_sessions, users RESTART IDENTITY CASCADE"
                )
            )
    finally:
        engine.dispose()
