import asyncio
from pathlib import Path

import httpx

from varys.api import create_app


def test_liveness_routes_return_ok_with_generated_request_id() -> None:
    responses = asyncio.run(_request_liveness_routes())

    for response in responses:
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.headers["X-Request-ID"]


def test_readiness_returns_service_unavailable_without_database() -> None:
    response = asyncio.run(_request("/api/health/ready"))

    assert response.status_code == 503
    assert response.json() == {"detail": "database URL is not configured"}


def test_current_user_rejects_request_without_a_session() -> None:
    response = asyncio.run(_request("/api/v1/auth/current-user"))

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_frontend_serves_bundle_and_preserves_api_namespace(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<app-root></app-root>", encoding="utf-8")
    (tmp_path / "main.js").write_text("console.log('varys')", encoding="utf-8")

    root, asset, missing_api = asyncio.run(_request_frontend(tmp_path))

    assert root.status_code == 200
    assert root.text == "<app-root></app-root>"
    assert asset.status_code == 200
    assert asset.text == "console.log('varys')"
    assert missing_api.status_code == 404


async def _request_liveness_routes() -> list[httpx.Response]:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return [
            await client.get("/api/health/live"),
            await client.get("/api/v1/health/live"),
        ]


async def _request(path: str) -> httpx.Response:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.get(path)


async def _request_frontend(
    frontend_directory: Path,
) -> tuple[httpx.Response, httpx.Response, httpx.Response]:
    app = create_app(frontend_directory=frontend_directory)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return (
            await client.get("/"),
            await client.get("/main.js"),
            await client.get("/api/v1/missing"),
        )
