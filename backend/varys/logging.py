"""Structured logging and request context."""

from __future__ import annotations

import json
import logging
import re
import sys
from contextvars import ContextVar, Token
from datetime import UTC, datetime
from typing import TextIO

_REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
_SENSITIVE_VALUE = re.compile(r"(?i)\b(password|secret|token|authorization)=([^\s,]+)")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "level": record.levelname,
            "service": getattr(record, "service", "app"),
            "request_id": _REQUEST_ID.get(),
            "run_id": getattr(record, "run_id", None),
            "user_id": getattr(record, "user_id", None),
            "source_type": getattr(record, "source_type", None),
            "message": _redact(record.getMessage()),
        }
        if record.exc_info is not None and record.exc_info[1] is not None:
            payload["exception_type"] = type(record.exc_info[1]).__name__
            payload["exception_message"] = _redact(str(record.exc_info[1]))
        return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def configure_logging(
    log_level: str, service: str, stream: TextIO | None = None
) -> None:
    handler = logging.StreamHandler(stream or sys.stdout)
    handler.setFormatter(JsonFormatter())
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)


def set_request_id(request_id: str) -> Token[str | None]:
    return _REQUEST_ID.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    _REQUEST_ID.reset(token)


def _redact(value: str) -> str:
    return _SENSITIVE_VALUE.sub(r"\1=<redacted>", value)
