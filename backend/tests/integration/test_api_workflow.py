import asyncio
import os
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from varys.api import create_app
from varys.auth import create_user
from varys.config import Settings
from varys.db import create_session_factory, upgrade_database
from varys.packages import (
    FindingSeverity,
    PackageArtifactInput,
    PackageIdentity,
    PackageKind,
    PackageProvenance,
    PackageSpecification,
    PreparationFinding,
    create_package,
    publish_package,
)
from varys.runs import Run
from varys.storage import StoragePaths, initialize_storage

_FIXTURES = Path(__file__).parents[1] / "golden" / "fixtures"


@pytest.mark.integration
def test_authenticated_run_and_package_apis_use_server_side_metadata(
    tmp_path: Path,
) -> None:
    database_url = os.getenv("VARYS_TEST_DATABASE_URL")
    if database_url is None:
        pytest.skip("VARYS_TEST_DATABASE_URL is not configured")
    upgrade_database(database_url)
    factory = create_session_factory(database_url)
    username = f"api-{os.urandom(8).hex()}"
    paths = StoragePaths.from_root(tmp_path / "data")
    initialize_storage(paths)
    with factory.begin() as database:
        create_user(database, username, "correct horse battery staple")

    app = create_app(_settings(database_url, paths.root))
    result = asyncio.run(_exercise_api(app, factory, username, paths))

    assert result["created_status"] == 202
    assert result["duplicate"] == {"detail": "RUN_ALREADY_EXISTS"}
    assert result["missing_csrf"] == {"detail": "CSRF validation failed"}
    assert result["event_count"] == 1
    assert result["control"] == {"detail": "RUN_CONTROL_NOT_ALLOWED"}
    assert result["package_path_exposed"] is False
    assert result["download"] == result["archive"]
    assert result["incomplete_download"] == {"detail": "Package is not available"}


async def _exercise_api(
    app: FastAPI,
    factory: sessionmaker[Session],
    username: str,
    paths: StoragePaths,
) -> dict[str, object]:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="https://testserver"
    ) as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"username": username, "password": "correct horse battery staple"},
        )
        assert login.status_code == 200
        csrf_token = login.json()["csrf_token"]
        headers = {"X-CSRF-Token": csrf_token}
        created = await client.post(
            "/api/v1/runs/daily", json={"trade_date": "2099-01-01"}, headers=headers
        )
        assert created.status_code == 202
        run_id = str(created.json()["id"])
        duplicate = await client.post(
            "/api/v1/runs/daily", json={"trade_date": "2099-01-01"}, headers=headers
        )
        missing_csrf = await client.post(
            "/api/v1/runs/daily", json={"trade_date": "2099-01-02"}
        )
        run = await client.get(f"/api/v1/runs/{run_id}")
        events = await client.get(f"/api/v1/runs/{run_id}/events")
        control = await client.post(f"/api/v1/runs/{run_id}/pause", headers=headers)
        assert run.status_code == 200
        assert run.json()["trade_date"] == "2099-01-01"

        with factory.begin() as database:
            persisted_run = database.get(Run, run_id)
            assert persisted_run is not None
            identity = PackageIdentity(uuid4(), PackageKind.DAILY, 1)
            package_record = create_package(database, persisted_run.id, identity)
            published = publish_package(
                database, paths, package_record, _specification(identity)
            )
            assert published is not None
            incomplete = create_package(
                database,
                persisted_run.id,
                PackageIdentity(uuid4(), PackageKind.DAILY, 2),
            )

        packages = await client.get("/api/v1/packages")
        package_response = await client.get(f"/api/v1/packages/{identity.id}")
        download = await client.get(f"/files/packages/{identity.id}")
        incomplete_download = await client.get(f"/files/packages/{incomplete.id}")
        assert packages.status_code == 200
        assert package_response.status_code == 200
        assert download.status_code == 200

        return {
            "created_status": created.status_code,
            "duplicate": duplicate.json(),
            "missing_csrf": missing_csrf.json(),
            "event_count": len(events.json()),
            "control": control.json(),
            "package_path_exposed": "relative_path" in package_response.json(),
            "download": download.content,
            "archive": (paths.root / published.relative_path).read_bytes(),
            "incomplete_download": incomplete_download.json(),
        }


def _settings(database_url: str, data_root: Path) -> Settings:
    return Settings(
        environment="test",
        log_level="INFO",
        api_host="127.0.0.1",
        api_port=8000,
        worker_id="test-worker",
        database_url=database_url,
        data_root=data_root,
        session_secret="test-session-secret-for-authenticated-api-workflow",
    )


def _specification(identity: PackageIdentity) -> PackageSpecification:
    return PackageSpecification(
        identity=identity,
        prepared_at=datetime(2026, 8, 14, 18, 30, tzinfo=UTC),
        provenance=PackageProvenance(
            configuration_fingerprint="a" * 64,
            raw_source_sha256=("b" * 64, "c" * 64),
            source_format_versions=(
                "capital-market-bhavcopy-udiff-v1",
                "nifty-indices-report-v1",
            ),
        ),
        artifacts=(
            PackageArtifactInput(
                "equity_market_data.csv", (_FIXTURES / "equity.csv").read_bytes()
            ),
            PackageArtifactInput(
                "index_ohlc.csv", (_FIXTURES / "index.csv").read_bytes()
            ),
        ),
        findings=(
            PreparationFinding(
                FindingSeverity.INFO,
                "COMPLETE",
                "PACKAGE",
                str(identity.id),
                "Fixture package complete",
            ),
        ),
    )
