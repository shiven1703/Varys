import asyncio

import httpx

from varys.api import create_app


def test_liveness_routes_return_ok_with_generated_request_id() -> None:
    responses = asyncio.run(_request_liveness_routes())

    for response in responses:
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
        assert response.headers["X-Request-ID"]


async def _request_liveness_routes() -> list[httpx.Response]:
    transport = httpx.ASGITransport(app=create_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return [
            await client.get("/api/health/live"),
            await client.get("/api/v1/health/live"),
        ]
