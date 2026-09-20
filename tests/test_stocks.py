import asyncio

import httpx

from app.main import app


def test_get_stock_returns_normalized_symbol() -> None:
    async def request_stock() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.get("/api/v1/stocks/600519.sh")

    response = asyncio.run(request_stock())

    assert response.status_code == 200
    assert response.json() == {"symbol": "600519.SH"}

def test_searches_stocks_by_name() -> None:
    async def request_stocks() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.get(
                "/api/v1/stocks",
                params={"query": "平安"},
            )

    response = asyncio.run(request_stocks())

    assert response.status_code == 200
    assert response.json() == [
        {
            "symbol": "000001.SZ",
            "name": "平安银行",
        }
    ]