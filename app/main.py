from fastapi import FastAPI, status
from pydantic import BaseModel, Field

from app.database import SessionLocal, Watchlist


class CreateWatchlistRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)


def create_app() -> FastAPI:
    application = FastAPI(
        title="A 股自选股风险监控 Agent",
        version="0.1.0",
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
            watchlist = Watchlist(name=payload.name)
            session.add(watchlist)
            session.commit()
            session.refresh(watchlist)

            return {
                "id": watchlist.id,
                "name": watchlist.name,
            }

    return application


app = create_app()
