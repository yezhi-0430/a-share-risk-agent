from fastapi import APIRouter, HTTPException, Query, status

from app.stocks.catalog import StockCatalog
from app.stocks.models import StockSummary


def create_stocks_router(catalog: StockCatalog) -> APIRouter:
    router = APIRouter(prefix="/stocks", tags=["stocks"])

    @router.get("", response_model=list[StockSummary])
    async def search_stocks(
        query: str = Query(min_length=1, max_length=40),
    ) -> list[StockSummary]:
        if not query.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="查询内容不能为空",
            )
        return catalog.search(query)

    return router

