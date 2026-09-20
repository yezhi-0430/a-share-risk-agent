import asyncio

import httpx

from app.main import create_app


class ApiClient:
    def __init__(self) -> None:
        self.app = create_app()

    def request(self, method: str, path: str, **kwargs: object) -> httpx.Response:
        async def send() -> httpx.Response:
            transport = httpx.ASGITransport(app=self.app)
            async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send())


def test_creates_and_lists_watchlist() -> None:
    client = ApiClient()

    created = client.request("POST", "/api/v1/watchlists", json={"name": "核心持仓"})
    listed = client.request("GET", "/api/v1/watchlists")

    assert created.status_code == 201
    assert created.json() == {"id": 1, "name": "核心持仓", "items": []}
    assert listed.json() == [{"id": 1, "name": "核心持仓", "items": []}]


def test_rejects_duplicate_watchlist_name() -> None:
    client = ApiClient()
    client.request("POST", "/api/v1/watchlists", json={"name": "半导体"})

    response = client.request("POST", "/api/v1/watchlists", json={"name": "半导体"})

    assert response.status_code == 409
    assert response.json() == {"detail": "自选股分组名称已存在"}


def test_rejects_blank_watchlist_name() -> None:
    response = ApiClient().request("POST", "/api/v1/watchlists", json={"name": "   "})

    assert response.status_code == 422


def test_adds_stock_to_watchlist() -> None:
    client = ApiClient()
    created = client.request("POST", "/api/v1/watchlists", json={"name": "消费"})

    response = client.request(
        "POST",
        f"/api/v1/watchlists/{created.json()['id']}/items",
        json={"symbol": "600519.SH"},
    )

    assert response.status_code == 201
    assert response.json()["items"] == [
        {"symbol": "600519.SH", "name": "贵州茅台", "market": "SH"}
    ]


def test_rejects_unknown_stock() -> None:
    client = ApiClient()
    created = client.request("POST", "/api/v1/watchlists", json={"name": "观察"})

    response = client.request(
        "POST",
        f"/api/v1/watchlists/{created.json()['id']}/items",
        json={"symbol": "999999.SH"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "未找到股票"}


def test_rejects_duplicate_stock_in_same_watchlist() -> None:
    client = ApiClient()
    created = client.request("POST", "/api/v1/watchlists", json={"name": "银行"})
    path = f"/api/v1/watchlists/{created.json()['id']}/items"
    client.request("POST", path, json={"symbol": "000001.SZ"})

    response = client.request("POST", path, json={"symbol": "000001.SZ"})

    assert response.status_code == 409
    assert response.json() == {"detail": "股票已在该分组中"}


def test_renames_watchlist() -> None:
    client = ApiClient()
    created = client.request("POST", "/api/v1/watchlists", json={"name": "旧名称"})

    response = client.request(
        "PATCH",
        f"/api/v1/watchlists/{created.json()['id']}",
        json={"name": "新名称"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "新名称"


def test_deletes_watchlist() -> None:
    client = ApiClient()
    created = client.request("POST", "/api/v1/watchlists", json={"name": "临时分组"})

    response = client.request("DELETE", f"/api/v1/watchlists/{created.json()['id']}")

    assert response.status_code == 204
    assert client.request("GET", "/api/v1/watchlists").json() == []


def test_removes_stock_from_watchlist() -> None:
    client = ApiClient()
    created = client.request("POST", "/api/v1/watchlists", json={"name": "消费"})
    item_path = f"/api/v1/watchlists/{created.json()['id']}/items/600519.SH"
    client.request(
        "POST",
        f"/api/v1/watchlists/{created.json()['id']}/items",
        json={"symbol": "600519.SH"},
    )

    response = client.request("DELETE", item_path)

    assert response.status_code == 204
    assert client.request("GET", "/api/v1/watchlists").json()[0]["items"] == []
