import logging
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StringConstraints
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.database import DailyPrice, SessionLocal, Stock
from app.risk_api import router as risk_router
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

class DailyPriceRequest(BaseModel):
    trade_date: date
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int = Field(ge=0)


def create_app() -> FastAPI:
    application = FastAPI(
        title="A 股自选股风险监控 Agent",
        version="0.1.0",
    )
    application.include_router(risk_router)

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

    @application.post("/api/v1/stocks/{symbol}/daily-prices", status_code=201)
    def import_daily_price(
    symbol: str,
    payload: DailyPriceRequest,
    ):
        with SessionLocal() as session:
            stock = session.scalar(
                select(Stock).where(Stock.symbol == symbol.upper())
            )

            if stock is None:
                raise HTTPException(status_code=404, detail="股票不存在")

            daily_price = DailyPrice(
                stock_id=stock.id,
                trade_date=payload.trade_date,
                open=payload.open,
                high=payload.high,
                low=payload.low,
                close=payload.close,
                volume=payload.volume,
            )

            session.add(daily_price)

            try:
                session.commit()
            except IntegrityError as exc:
                session.rollback()
                raise HTTPException(
                    status_code=409,
                    detail="该股票当天的日线数据已存在",
                ) from exc

        return {"symbol": symbol.upper()}

    @application.get("/api/v1/stocks/{symbol}/daily-prices")
    def get_daily_prices(symbol: str) -> list[dict[str, object]]:
        with SessionLocal() as session:
            stock = session.scalar(
                select(Stock).where(Stock.symbol == symbol.upper())
            )

            if stock is None:
                raise HTTPException(status_code=404, detail="股票不存在")

            daily_prices = session.scalars(
                select(DailyPrice)
                .where(DailyPrice.stock_id == stock.id)
                .order_by(DailyPrice.trade_date.desc())
            ).all()

            return [
                {
                    "trade_date": item.trade_date.isoformat(),
                    "open": str(item.open),
                    "high": str(item.high),
                    "low": str(item.low),
                    "close": str(item.close),
                    "volume": item.volume,
                }
                for item in daily_prices
            ]

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
