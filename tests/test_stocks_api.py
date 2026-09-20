import asyncio

import httpx

from app.main import create_app


def request(method: str, path: str, **kwargs: object) -> httpx.Response:
    async def send() -> httpx.Response:
        app = create_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            return await client.request(method, path, **kwargs)

    return asyncio.run(send())


def test_searches_stock_by_code() -> None:
    response = request("GET", "/api/v1/stocks", params={"query": "600519"})

    assert response.status_code == 200
    assert response.json() == [
        {"symbol": "600519.SH", "name": "贵州茅台", "market": "SH"}
    ]


def test_searches_stock_by_name() -> None:
    response = request("GET", "/api/v1/stocks", params={"query": "平安"})

    assert response.status_code == 200
    assert response.json() == [
        {"symbol": "000001.SZ", "name": "平安银行", "market": "SZ"},
        {"symbol": "601318.SH", "name": "中国平安", "market": "SH"},
    ]


def test_rejects_blank_stock_query() -> None:
    response = request("GET", "/api/v1/stocks", params={"query": "   "})

    assert response.status_code == 422
