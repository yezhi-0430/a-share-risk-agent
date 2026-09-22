import asyncio

import httpx
import pytest

from app import main as main_module
from app.database import SessionLocal, Watchlist
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
    body = response.json()

    try:
        assert isinstance(body["id"], int)
        assert body["name"] == "核心持仓"
    finally:
        with SessionLocal() as session:
            saved_watchlist = session.get(
                Watchlist,
                body["id"],
            )
            if saved_watchlist is not None:
                session.delete(saved_watchlist)
                session.commit()


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


def test_create_watchlist_saves_to_database() -> None:
    async def create_watchlist() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.post(
                "/api/v1/watchlists",
                json={"name": "长期观察"},
            )

    response = asyncio.run(create_watchlist())
    watchlist_id = response.json()["id"]

    try:
        with SessionLocal() as session:
            saved_watchlist = session.get(
                Watchlist,
                watchlist_id,
            )

            assert saved_watchlist is not None
            assert saved_watchlist.name == "长期观察"
    finally:
        with SessionLocal() as session:
            saved_watchlist = session.get(
                Watchlist,
                watchlist_id,
            )
            if saved_watchlist is not None:
                session.delete(saved_watchlist)
                session.commit()


def test_lists_watchlists() -> None:
    async def request_watchlists() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.get("/api/v1/watchlists")

    response = asyncio.run(request_watchlists())

    assert response.status_code == 200
    assert response.json() == []


def test_lists_saved_watchlist() -> None:
    with SessionLocal() as session:
        watchlist = Watchlist(name="风险观察")
        session.add(watchlist)
        session.commit()
        session.refresh(watchlist)
        watchlist_id = watchlist.id

    async def request_watchlists() -> httpx.Response:
        transport = httpx.ASGITransport(app=app)

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.get("/api/v1/watchlists")

    try:
        response = asyncio.run(request_watchlists())

        assert response.status_code == 200
        assert {
            "id": watchlist_id,
            "name": "风险观察",
        } in response.json()
    finally:
        with SessionLocal() as session:
            saved_watchlist = session.get(Watchlist, watchlist_id)
            if saved_watchlist is not None:
                session.delete(saved_watchlist)
                session.commit()


def test_unexpected_database_error_returns_safe_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_to_create_watchlist(
        session: object,
        name: str,
    ) -> None:
        raise RuntimeError("database connection details")

    monkeypatch.setattr(
        main_module,
        "save_watchlist",
        fail_to_create_watchlist,
    )

    async def create_watchlist() -> httpx.Response:
        transport = httpx.ASGITransport(
            app=app,
            raise_app_exceptions=False,
        )

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.post(
                "/api/v1/watchlists",
                json={"name": "异常测试"},
            )

    response = asyncio.run(create_watchlist())

    assert response.status_code == 500
    assert response.json() == {"detail": "服务器内部错误"}
    assert "database connection details" not in response.text
