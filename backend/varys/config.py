"""Validated process configuration."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

_KNOWN_SETTINGS = frozenset(
    {
        "VARYS_API_HOST",
        "VARYS_API_PORT",
        "VARYS_DATA_ROOT",
        "VARYS_DATABASE_URL",
        "VARYS_ENVIRONMENT",
        "VARYS_LOG_LEVEL",
        "VARYS_SESSION_SECRET",
        "VARYS_WORKER_ID",
    }
)
_LOG_LEVELS = frozenset({"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"})


@dataclass(frozen=True, slots=True)
class Settings:
    environment: str
    log_level: str
    api_host: str
    api_port: int
    worker_id: str
    database_url: str | None
    data_root: Path | None
    session_secret: str | None


def load_settings(environ: Mapping[str, str] | None = None) -> Settings:
    values = os.environ if environ is None else environ
    unknown_settings = sorted(
        key for key in values if key.startswith("VARYS_") and key not in _KNOWN_SETTINGS
    )
    if unknown_settings:
        raise ValueError(f"Unknown VARYS_ setting: {', '.join(unknown_settings)}")

    log_level = values.get("VARYS_LOG_LEVEL", "INFO").upper()
    if log_level not in _LOG_LEVELS:
        raise ValueError("VARYS_LOG_LEVEL must be a standard Python log level")

    api_port = _parse_port(values.get("VARYS_API_PORT", "8000"))
    return Settings(
        environment=values.get("VARYS_ENVIRONMENT", "development"),
        log_level=log_level,
        api_host=values.get("VARYS_API_HOST", "127.0.0.1"),
        api_port=api_port,
        worker_id=values.get("VARYS_WORKER_ID", "varys-worker"),
        database_url=values.get("VARYS_DATABASE_URL"),
        data_root=_optional_path(values.get("VARYS_DATA_ROOT")),
        session_secret=values.get("VARYS_SESSION_SECRET"),
    )


def _parse_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as error:
        raise ValueError("VARYS_API_PORT must be an integer") from error
    if not 1 <= port <= 65535:
        raise ValueError("VARYS_API_PORT must be between 1 and 65535")
    return port


def _optional_path(value: str | None) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if not path.is_absolute():
        raise ValueError("VARYS_DATA_ROOT must be an absolute path")
    return path
