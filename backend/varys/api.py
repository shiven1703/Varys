"""FastAPI process entrypoint."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Awaitable, Callable
from mimetypes import guess_type
from pathlib import Path
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response

from varys.config import Settings, load_settings
from varys.db import check_database_readiness
from varys.logging import configure_logging, reset_request_id, set_request_id
from varys.storage import check_storage_readiness

_LOGGER = logging.getLogger("varys.api")


def create_app(
    settings: Settings | None = None, frontend_directory: Path | None = None
) -> FastAPI:
    application_settings = settings or load_settings()
    app = FastAPI(title="Varys")

    @app.middleware("http")
    async def request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        request_id = str(uuid4())
        token = set_request_id(request_id)
        try:
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            _LOGGER.info(
                "request completed",
                extra={"service": "app", "status_code": response.status_code},
            )
            return response
        finally:
            reset_request_id(token)

    @app.get("/api/health/live")
    @app.get("/api/v1/health/live")
    async def live() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/health/ready")
    async def ready() -> dict[str, str]:
        database_readiness = check_database_readiness(application_settings.database_url)
        if not database_readiness.ready:
            raise HTTPException(status_code=503, detail=database_readiness.reason)
        storage_readiness = check_storage_readiness(application_settings.data_root)
        if not storage_readiness.ready:
            raise HTTPException(status_code=503, detail=storage_readiness.reason)
        return {"status": "ok"}

    if frontend_directory is not None and (frontend_directory / "index.html").is_file():

        @app.get("/{path:path}", include_in_schema=False)
        async def frontend(path: str) -> Response:
            if path.startswith(("api/", "files/")):
                raise HTTPException(status_code=404, detail="Not found")
            requested_file = (frontend_directory / path).resolve()
            is_bundle_file = (
                requested_file.is_relative_to(frontend_directory.resolve())
                and requested_file.is_file()
            )
            if is_bundle_file:
                return _static_response(requested_file)
            return _static_response(frontend_directory / "index.html")

    app.state.settings = application_settings
    return app


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    settings = load_settings()
    configure_logging(settings.log_level, service="app")
    app = create_app(settings, Path(__file__).with_name("frontend"))
    if arguments.check:
        _LOGGER.info("app bootstrap complete", extra={"service": "app"})
        return 0
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_config=None)
    return 0


def _static_response(path: Path) -> Response:
    media_type, _ = guess_type(path.name)
    return Response(content=path.read_bytes(), media_type=media_type)


if __name__ == "__main__":
    raise SystemExit(main())
