from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest
from sqlalchemy.exc import IntegrityError

from varys import cli


class _Transaction:
    def __init__(self, database: object) -> None:
        self.database = database

    def __enter__(self) -> object:
        return self.database

    def __exit__(self, *_arguments: object) -> None:
        return None


class _Factory:
    def __init__(self, database: object) -> None:
        self.database = database

    def begin(self) -> _Transaction:
        return _Transaction(self.database)


class _Database:
    def __init__(self, error: IntegrityError | None = None) -> None:
        self.error = error
        self.flushed = False

    def flush(self) -> None:
        self.flushed = True
        if self.error is not None:
            raise self.error


def _configure_command(monkeypatch: pytest.MonkeyPatch, database: _Database) -> None:
    monkeypatch.setattr(
        sys, "argv", ["varys", "create-admin", "--username", "operator"]
    )
    monkeypatch.setattr(
        "varys.cli.getpass.getpass", lambda _prompt: "safe-password-123"
    )
    monkeypatch.setattr(
        cli, "load_settings", lambda: SimpleNamespace(database_url="test")
    )
    monkeypatch.setattr(cli, "create_session_factory", lambda _url: _Factory(database))
    monkeypatch.setattr(cli, "create_user", lambda *_arguments: None)


def test_create_admin_flushes_before_committing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database = _Database()
    _configure_command(monkeypatch, database)

    assert cli.main() == 0
    assert database.flushed


def test_create_admin_reports_duplicate_username_without_traceback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    database = _Database(IntegrityError("INSERT", {}, Exception("duplicate username")))
    _configure_command(monkeypatch, database)

    with pytest.raises(SystemExit, match="2"):
        cli.main()

    assert "duplicate username" in capsys.readouterr().err
