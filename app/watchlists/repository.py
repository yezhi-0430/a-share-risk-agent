from app.stocks.models import StockSummary
from app.watchlists.models import Watchlist


class DuplicateWatchlistNameError(Exception):
    pass


class WatchlistNotFoundError(Exception):
    pass


class DuplicateWatchlistItemError(Exception):
    pass


class WatchlistItemNotFoundError(Exception):
    pass


class MemoryWatchlistRepository:
    def __init__(self) -> None:
        self._watchlists: dict[int, Watchlist] = {}
        self._next_id = 1

    def list_all(self) -> list[Watchlist]:
        return [watchlist.model_copy(deep=True) for watchlist in self._watchlists.values()]

    def create(self, name: str) -> Watchlist:
        if any(watchlist.name == name for watchlist in self._watchlists.values()):
            raise DuplicateWatchlistNameError

        watchlist = Watchlist(id=self._next_id, name=name, items=[])
        self._watchlists[watchlist.id] = watchlist
        self._next_id += 1
        return watchlist.model_copy(deep=True)

    def rename(self, watchlist_id: int, name: str) -> Watchlist:
        watchlist = self._watchlists.get(watchlist_id)
        if watchlist is None:
            raise WatchlistNotFoundError
        if any(
            item.id != watchlist_id and item.name == name
            for item in self._watchlists.values()
        ):
            raise DuplicateWatchlistNameError

        watchlist.name = name
        return watchlist.model_copy(deep=True)

    def delete(self, watchlist_id: int) -> None:
        if self._watchlists.pop(watchlist_id, None) is None:
            raise WatchlistNotFoundError

    def add_item(self, watchlist_id: int, stock: StockSummary) -> Watchlist:
        watchlist = self._watchlists.get(watchlist_id)
        if watchlist is None:
            raise WatchlistNotFoundError
        if any(item.symbol == stock.symbol for item in watchlist.items):
            raise DuplicateWatchlistItemError

        watchlist.items.append(stock)
        return watchlist.model_copy(deep=True)

    def remove_item(self, watchlist_id: int, symbol: str) -> None:
        watchlist = self._watchlists.get(watchlist_id)
        if watchlist is None:
            raise WatchlistNotFoundError

        matching_item = next((item for item in watchlist.items if item.symbol == symbol), None)
        if matching_item is None:
            raise WatchlistItemNotFoundError
        watchlist.items.remove(matching_item)
