"""Dedicated worker process entrypoint."""

from __future__ import annotations

import argparse
import logging

from varys.config import load_settings
from varys.logging import configure_logging

_LOGGER = logging.getLogger("varys.worker")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    settings = load_settings()
    configure_logging(settings.log_level, service="worker")
    _LOGGER.info(
        "worker bootstrap complete",
        extra={"service": "worker", "worker_id": settings.worker_id},
    )
    if arguments.check:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
