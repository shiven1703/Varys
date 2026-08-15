"""FastAPI process entrypoint."""

from __future__ import annotations

import argparse
import logging
from collections.abc import Awaitable, Callable, Generator
from contextlib import AbstractContextManager
from datetime import UTC, date, datetime
from mimetypes import guess_type
from pathlib import Path
from uuid import UUID, uuid4

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from varys.auth import (
    CSRF_HEADER_NAME,
    SESSION_COOKIE_NAME,
    User,
    current_user,
    login,
    revoke_session,
    validate_csrf_token,
)
from varys.config import Settings, load_settings
from varys.db import check_database_readiness, create_session_factory
from varys.logging import configure_logging, reset_request_id, set_request_id
from varys.packages import Package, PackageFile, PackageState
from varys.runs import (
    RequestedAction,
    Run,
    RunEvent,
    create_daily_run,
    request_action,
    resume_paused_run,
)
from varys.storage import StoragePaths, check_storage_readiness, sha256_file

_LOGGER = logging.getLogger("varys.api")


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: str
    username: str


class LoginResponse(BaseModel):
    user: UserResponse
    csrf_token: str


class DailyRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    trade_date: date


class RunResponse(BaseModel):
    id: str
    kind: str
    trade_date: str | None
    state: str
    requested_action: str | None
    created_at: str
    updated_at: str


class RunEventResponse(BaseModel):
    sequence: int
    event_type: str
    from_state: str | None
    to_state: str | None
    created_at: str


class PackageFileResponse(BaseModel):
    name: str
    sha256: str
    size_bytes: int
    row_count: int | None


class PackageResponse(BaseModel):
    id: str
    run_id: str
    kind: str
    version: int
    state: str
    size_bytes: int | None
    sha256: str | None
    files: list[PackageFileResponse]


def create_app(
    settings: Settings | None = None, frontend_directory: Path | None = None
) -> FastAPI:
    application_settings = settings or load_settings()
    app = FastAPI(title="Varys")
    app.state.settings = application_settings
    app.state.session_factory = _session_factory(application_settings)

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

    def database_session() -> Generator[Session, None, None]:
        factory: sessionmaker[Session] | None = app.state.session_factory
        if factory is None:
            raise HTTPException(
                status_code=503, detail="authentication is not configured"
            )
        with factory.begin() as database:
            yield database

    def authenticated_user(
        request: Request, database: Session = Depends(database_session)
    ) -> User:
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        if session_token is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        user = current_user(
            database, session_token, _session_secret(application_settings)
        )
        if user is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        return user

    def csrf_protected(
        request: Request,
        database: Session = Depends(database_session),
        _user: User = Depends(authenticated_user),
    ) -> None:
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        csrf_token = request.headers.get(CSRF_HEADER_NAME)
        if (
            session_token is None
            or csrf_token is None
            or not validate_csrf_token(
                database,
                session_token,
                csrf_token,
                _session_secret(application_settings),
            )
        ):
            raise HTTPException(status_code=403, detail="CSRF validation failed")

    @app.post("/api/v1/auth/login", response_model=LoginResponse)
    async def login_endpoint(
        credentials: LoginRequest,
        response: Response,
        database: Session = Depends(database_session),
    ) -> LoginResponse:
        session_secret = _session_secret(application_settings)
        authenticated = login(
            database, credentials.username, credentials.password, session_secret
        )
        if authenticated is None:
            raise HTTPException(status_code=401, detail="Invalid username or password")
        user, session_token, csrf_token = authenticated
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=session_token,
            httponly=True,
            secure=True,
            samesite="lax",
            max_age=7 * 24 * 60 * 60,
            path="/",
        )
        return LoginResponse(user=_user_response(user), csrf_token=csrf_token)

    @app.get("/api/v1/auth/current-user", response_model=UserResponse)
    async def current_user_endpoint(request: Request) -> UserResponse:
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        if session_token is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        with _database_transaction(app.state.session_factory) as database:
            user = current_user(
                database, session_token, _session_secret(application_settings)
            )
            if user is None:
                raise HTTPException(status_code=401, detail="Authentication required")
            return _user_response(user)

    @app.post(
        "/api/v1/runs/daily",
        response_model=RunResponse,
        status_code=status.HTTP_202_ACCEPTED,
    )
    async def create_daily_run_endpoint(
        payload: DailyRunRequest,
        database: Session = Depends(database_session),
        _user: User = Depends(csrf_protected),
    ) -> RunResponse:
        run = create_daily_run(database, payload.trade_date)
        if run is None:
            raise HTTPException(status_code=409, detail="RUN_ALREADY_EXISTS")
        return _run_response(run)

    @app.get("/api/v1/runs/{run_id}", response_model=RunResponse)
    async def read_run_endpoint(
        run_id: UUID,
        database: Session = Depends(database_session),
        _user: User = Depends(authenticated_user),
    ) -> RunResponse:
        return _run_response(_required_run(database, run_id))

    @app.get("/api/v1/runs/{run_id}/events", response_model=list[RunEventResponse])
    async def read_run_events_endpoint(
        run_id: UUID,
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=100, ge=1, le=100),
        database: Session = Depends(database_session),
        _user: User = Depends(authenticated_user),
    ) -> list[RunEventResponse]:
        _required_run(database, run_id)
        events = database.scalars(
            select(RunEvent)
            .where(RunEvent.run_id == run_id)
            .order_by(RunEvent.sequence)
            .offset(offset)
            .limit(limit)
        )
        return [_run_event_response(event) for event in events]

    @app.post("/api/v1/runs/{run_id}/pause", response_model=RunResponse)
    async def pause_run_endpoint(
        run_id: UUID,
        database: Session = Depends(database_session),
        _user: User = Depends(csrf_protected),
    ) -> RunResponse:
        run = _required_run(database, run_id)
        if not request_action(database, run, RequestedAction.PAUSE):
            raise HTTPException(status_code=409, detail="RUN_CONTROL_NOT_ALLOWED")
        return _run_response(run)

    @app.post("/api/v1/runs/{run_id}/cancel", response_model=RunResponse)
    async def cancel_run_endpoint(
        run_id: UUID,
        database: Session = Depends(database_session),
        _user: User = Depends(csrf_protected),
    ) -> RunResponse:
        run = _required_run(database, run_id)
        if not request_action(database, run, RequestedAction.CANCEL):
            raise HTTPException(status_code=409, detail="RUN_CONTROL_NOT_ALLOWED")
        return _run_response(run)

    @app.post("/api/v1/runs/{run_id}/resume", response_model=RunResponse)
    async def resume_run_endpoint(
        run_id: UUID,
        database: Session = Depends(database_session),
        _user: User = Depends(csrf_protected),
    ) -> RunResponse:
        run = _required_run(database, run_id)
        if not resume_paused_run(database, run):
            raise HTTPException(status_code=409, detail="RUN_CONTROL_NOT_ALLOWED")
        return _run_response(run)

    @app.get("/api/v1/packages", response_model=list[PackageResponse])
    async def list_packages_endpoint(
        database: Session = Depends(database_session),
        _user: User = Depends(authenticated_user),
    ) -> list[PackageResponse]:
        packages = database.scalars(select(Package).order_by(Package.created_at.desc()))
        return [_package_response(database, package) for package in packages]

    @app.get("/api/v1/packages/{package_id}", response_model=PackageResponse)
    async def read_package_endpoint(
        package_id: UUID,
        database: Session = Depends(database_session),
        _user: User = Depends(authenticated_user),
    ) -> PackageResponse:
        return _package_response(database, _required_package(database, package_id))

    @app.get("/files/packages/{package_id}")
    async def download_package_endpoint(
        package_id: UUID,
        database: Session = Depends(database_session),
        _user: User = Depends(authenticated_user),
    ) -> FileResponse:
        package = _required_package(database, package_id)
        path = _verified_download_path(application_settings, package)
        return FileResponse(
            path,
            media_type="application/zip",
            filename=f"varys-{package.id}.zip",
        )

    @app.post("/api/v1/auth/logout", status_code=204)
    async def logout_endpoint(
        request: Request,
        response: Response,
    ) -> Response:
        session_token = request.cookies.get(SESSION_COOKIE_NAME)
        csrf_token = request.headers.get(CSRF_HEADER_NAME)
        if session_token is None or csrf_token is None:
            raise HTTPException(status_code=401, detail="Authentication required")
        with _database_transaction(app.state.session_factory) as database:
            if not revoke_session(
                database,
                session_token,
                csrf_token,
                _session_secret(application_settings),
            ):
                raise HTTPException(status_code=403, detail="CSRF validation failed")
        response.delete_cookie(SESSION_COOKIE_NAME, path="/")
        return response

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


def _session_factory(settings: Settings) -> sessionmaker[Session] | None:
    if settings.database_url is None:
        return None
    return create_session_factory(settings.database_url)


def _session_secret(settings: Settings) -> str:
    if not settings.session_secret:
        raise HTTPException(status_code=503, detail="authentication is not configured")
    return settings.session_secret


def _database_transaction(
    factory: sessionmaker[Session] | None,
) -> AbstractContextManager[Session, bool | None]:
    if factory is None:
        raise HTTPException(status_code=503, detail="authentication is not configured")
    return factory.begin()


def _user_response(user: User) -> UserResponse:
    return UserResponse(id=str(user.id), username=user.username)


def _run_response(run: Run) -> RunResponse:
    return RunResponse(
        id=str(run.id),
        kind=run.kind,
        trade_date=run.trade_date.isoformat() if run.trade_date else None,
        state=run.state,
        requested_action=run.requested_action,
        created_at=_timestamp(run.created_at),
        updated_at=_timestamp(run.updated_at),
    )


def _run_event_response(event: RunEvent) -> RunEventResponse:
    return RunEventResponse(
        sequence=event.sequence,
        event_type=event.event_type,
        from_state=event.from_state,
        to_state=event.to_state,
        created_at=_timestamp(event.created_at),
    )


def _package_response(database: Session, package: Package) -> PackageResponse:
    files = database.scalars(
        select(PackageFile)
        .where(PackageFile.package_id == package.id)
        .order_by(PackageFile.name)
    )
    return PackageResponse(
        id=str(package.id),
        run_id=str(package.run_id),
        kind=package.kind,
        version=package.version,
        state=package.state,
        size_bytes=package.size_bytes,
        sha256=package.sha256,
        files=[
            PackageFileResponse(
                name=file.name,
                sha256=file.sha256,
                size_bytes=file.size_bytes,
                row_count=file.row_count,
            )
            for file in files
        ],
    )


def _required_run(database: Session, run_id: UUID) -> Run:
    run = database.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


def _required_package(database: Session, package_id: UUID) -> Package:
    package = database.get(Package, package_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Package not found")
    return package


def _verified_download_path(settings: Settings, package: Package) -> Path:
    if package.state not in (PackageState.READY, PackageState.READY_WITH_WARNINGS):
        raise HTTPException(status_code=404, detail="Package is not available")
    if settings.data_root is None or package.relative_path is None:
        raise HTTPException(status_code=404, detail="Package is not available")
    paths = StoragePaths.from_root(settings.data_root)
    expected_path = paths.ready_package(package.kind, str(package.id))
    if package.relative_path != str(expected_path.relative_to(paths.root)):
        raise HTTPException(status_code=404, detail="Package is not available")
    if (
        not expected_path.is_file()
        or package.size_bytes != expected_path.stat().st_size
        or package.sha256 != sha256_file(expected_path)
    ):
        raise HTTPException(status_code=404, detail="Package is not available")
    return expected_path


def _timestamp(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


if __name__ == "__main__":
    raise SystemExit(main())
