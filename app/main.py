import logging
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StringConstraints

from app.database import SessionLocal
from app.watchlists.repository import (
    DuplicateStockInWatchlistError,
    StockNotInWatchlistError,
    WatchlistNotFoundError,
    add_stock_to_watchlist,
    get_watchlists,
    remove_stock_from_watchlist,
)
from app.watchlists.repository import create_watchlist as save_watchlist

logger = logging.getLogger(__name__)


class CreateWatchlistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)


class AddStockRequest(BaseModel):
    symbol: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


def create_app() -> FastAPI:
    application = FastAPI(
        title="A 股自选股风险监控 Agent",
        version="0.1.0",
    )

    @application.exception_handler(Exception)
    async def handle_unexpected_error(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("未处理的应用异常")
        return JSONResponse(
            status_code=500,
            content={"detail": "服务器内部错误"},
        )

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @application.get("/api/v1/stocks/{symbol}", tags=["stocks"])
    async def get_stock(symbol: str) -> dict[str, str]:
        return {"symbol": symbol.upper()}

    @application.get("/api/v1/stocks", tags=["stocks"])
    async def search_stocks(query: str) -> list[dict[str, str]]:
        stocks = [
            {
                "symbol": "000001.SZ",
                "name": "平安银行",
            }
        ]

        return [
            stock for stock in stocks if query in stock["name"] or query.upper() in stock["symbol"]
        ]

    @application.post(
        "/api/v1/watchlists",
        tags=["watchlists"],
        status_code=status.HTTP_201_CREATED,
    )
    def create_watchlist(
        payload: CreateWatchlistRequest,
    ) -> dict[str, int | str]:
        with SessionLocal() as session:
            watchlist = save_watchlist(session, payload.name)
            return {
                "id": watchlist.id,
                "name": watchlist.name,
            }

    @application.get("/api/v1/watchlists", tags=["watchlists"])
    def list_watchlists() -> list[dict[str, int | str]]:
        with SessionLocal() as session:
            watchlists = get_watchlists(session)

            return [
                {
                    "id": watchlist.id,
                    "name": watchlist.name,
                }
                for watchlist in watchlists
            ]

    @application.post(
        "/api/v1/watchlists/{watchlist_id}/stocks",
        tags=["watchlists"],
        status_code=status.HTTP_201_CREATED,
    )
    def add_stock(
        watchlist_id: int,
        payload: AddStockRequest,
    ) -> dict[str, str]:
        with SessionLocal() as session:
            try:
                stock = add_stock_to_watchlist(
                    session,
                    watchlist_id,
                    payload.symbol,
                    payload.name,
                )
            except WatchlistNotFoundError as exc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="自选组不存在",
                ) from exc
            except DuplicateStockInWatchlistError as exc:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="该股票已在自选组中",
                ) from exc

            return {
                "symbol": stock.symbol,
                "name": stock.name,
            }

    @application.delete(
        "/api/v1/watchlists/{watchlist_id}/stocks/{symbol}",
        tags=["watchlists"],
        status_code=status.HTTP_204_NO_CONTENT,
    )
    def remove_stock(watchlist_id: int, symbol: str) -> None:
        with SessionLocal() as session:
            try:
                remove_stock_from_watchlist(session, watchlist_id, symbol)
            except WatchlistNotFoundError as exc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="自选组不存在",
                ) from exc
            except StockNotInWatchlistError as exc:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="自选组中不存在该股票",
                ) from exc

    return application


app = create_app()
