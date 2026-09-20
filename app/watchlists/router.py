from fastapi import APIRouter, HTTPException, Response, status

from app.stocks.catalog import StockCatalog
from app.watchlists.models import (
    AddWatchlistItemRequest,
    CreateWatchlistRequest,
    UpdateWatchlistRequest,
    Watchlist,
)
from app.watchlists.repository import (
    DuplicateWatchlistItemError,
    DuplicateWatchlistNameError,
    MemoryWatchlistRepository,
    WatchlistItemNotFoundError,
    WatchlistNotFoundError,
)


def create_watchlists_router(
    repository: MemoryWatchlistRepository,
    catalog: StockCatalog,
) -> APIRouter:
    router = APIRouter(prefix="/watchlists", tags=["watchlists"])

    @router.get("", response_model=list[Watchlist])
    async def list_watchlists() -> list[Watchlist]:
        return repository.list_all()

    @router.post("", response_model=Watchlist, status_code=status.HTTP_201_CREATED)
    async def create_watchlist(payload: CreateWatchlistRequest) -> Watchlist:
        try:
            return repository.create(payload.name)
        except DuplicateWatchlistNameError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="自选股分组名称已存在",
            ) from error

    @router.patch("/{watchlist_id}", response_model=Watchlist)
    async def rename_watchlist(
        watchlist_id: int,
        payload: UpdateWatchlistRequest,
    ) -> Watchlist:
        try:
            return repository.rename(watchlist_id, payload.name)
        except WatchlistNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到自选股分组",
            ) from error
        except DuplicateWatchlistNameError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="自选股分组名称已存在",
            ) from error

    @router.delete("/{watchlist_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_watchlist(watchlist_id: int) -> Response:
        try:
            repository.delete(watchlist_id)
        except WatchlistNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到自选股分组",
            ) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    @router.post(
        "/{watchlist_id}/items",
        response_model=Watchlist,
        status_code=status.HTTP_201_CREATED,
    )
    async def add_watchlist_item(
        watchlist_id: int,
        payload: AddWatchlistItemRequest,
    ) -> Watchlist:
        stock = catalog.get(payload.symbol)
        if stock is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到股票")

        try:
            return repository.add_item(watchlist_id, stock)
        except WatchlistNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到自选股分组",
            ) from error
        except DuplicateWatchlistItemError as error:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="股票已在该分组中",
            ) from error

    @router.delete(
        "/{watchlist_id}/items/{symbol}",
        status_code=status.HTTP_204_NO_CONTENT,
    )
    async def remove_watchlist_item(watchlist_id: int, symbol: str) -> Response:
        try:
            repository.remove_item(watchlist_id, symbol.upper())
        except WatchlistNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="未找到自选股分组",
            ) from error
        except WatchlistItemNotFoundError as error:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="股票不在该分组中",
            ) from error
        return Response(status_code=status.HTTP_204_NO_CONTENT)

    return router
