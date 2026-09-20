import asyncio

import httpx

from app.main import app


def test_creates_watchlist_from_request_body() -> None:
    async def create_watchlist() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.post(
                "/api/v1/watchlists",
                json={"name": "核心持仓"},
            )

    response = asyncio.run(create_watchlist())

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "name": "核心持仓",
    }


def test_rejects_empty_watchlist_name() -> None:
    async def create_watchlist() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.post(
                "/api/v1/watchlists",
                json={"name": ""},
            )

    response = asyncio.run(create_watchlist())

    assert response.status_code == 422