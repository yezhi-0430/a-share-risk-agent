import asyncio

import httpx

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
