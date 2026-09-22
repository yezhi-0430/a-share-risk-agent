import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.database import SessionLocal
from app.watchlists.repository import create_watchlist as save_watchlist
from app.watchlists.repository import get_watchlists

logger = logging.getLogger(__name__)


class CreateWatchlistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)


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

    return application


app = create_app()
