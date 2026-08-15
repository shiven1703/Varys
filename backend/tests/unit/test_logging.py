import json
import logging
from io import StringIO

from varys.logging import configure_logging, reset_request_id, set_request_id


def test_json_logs_include_request_context_and_redact_secret() -> None:
    stream = StringIO()
    configure_logging("INFO", service="test", stream=stream)
    token = set_request_id("request-123")
    try:
        logging.getLogger("varys.test").info("password=%s", "not-for-logs")
    finally:
        reset_request_id(token)

    payload = json.loads(stream.getvalue())
    assert payload["request_id"] == "request-123"
    assert payload["message"] == "password=<redacted>"
    assert "not-for-logs" not in stream.getvalue()


def test_json_logs_include_redacted_exception_diagnostics() -> None:
    stream = StringIO()
    configure_logging("INFO", service="worker", stream=stream)

    try:
        raise ValueError("token=not-for-logs")
    except ValueError:
        logging.getLogger("varys.worker").exception("fixture run failed")

    payload = json.loads(stream.getvalue())
    assert payload["exception_type"] == "ValueError"
    assert payload["exception_message"] == "token=<redacted>"
    assert "not-for-logs" not in stream.getvalue()
