from fastapi import FastAPI

from app.stocks.catalog import create_demo_catalog
from app.stocks.router import create_stocks_router
from app.watchlists.repository import MemoryWatchlistRepository
from app.watchlists.router import create_watchlists_router


def create_app() -> FastAPI:
    catalog = create_demo_catalog()
    watchlist_repository = MemoryWatchlistRepository()
    application = FastAPI(
        title="A 股自选股风险监控 Agent",
        version="0.1.0",
    )

    @application.get("/health", tags=["system"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    application.include_router(create_stocks_router(catalog), prefix="/api/v1")
    application.include_router(
        create_watchlists_router(watchlist_repository, catalog),
        prefix="/api/v1",
    )

    return application


app = create_app()
