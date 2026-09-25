from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Stock, Watchlist, WatchlistItem


class WatchlistNotFoundError(Exception):
    pass


class DuplicateStockInWatchlistError(Exception):
    pass


class StockNotInWatchlistError(Exception):
    pass


def create_watchlist(session: Session, name: str) -> Watchlist:
    watchlist = Watchlist(name=name)
    session.add(watchlist)
    session.commit()
    session.refresh(watchlist)
    return watchlist


def get_watchlists(session: Session) -> list[Watchlist]:
    statement = select(Watchlist).order_by(Watchlist.id)
    return list(session.scalars(statement).all())


def add_stock_to_watchlist(
    session: Session,
    watchlist_id: int,
    symbol: str,
    name: str,
) -> Stock:
    watchlist = session.get(Watchlist, watchlist_id)
    if watchlist is None:
        raise WatchlistNotFoundError

    stock_statement = select(Stock).where(Stock.symbol == symbol)
    stock = session.scalar(stock_statement)
    if stock is None:
        stock = Stock(symbol=symbol, name=name)
        session.add(stock)
        session.flush()

    item_statement = select(WatchlistItem).where(
        WatchlistItem.watchlist_id == watchlist_id,
        WatchlistItem.stock_id == stock.id,
    )
    if stock.id is not None and session.scalar(item_statement) is not None:
        raise DuplicateStockInWatchlistError

    session.add(
        WatchlistItem(
            watchlist_id=watchlist_id,
            stock_id=stock.id,
        )
    )
    session.commit()
    session.refresh(stock)
    return stock


def remove_stock_from_watchlist(
    session: Session,
    watchlist_id: int,
    symbol: str,
) -> None:
    watchlist = session.get(Watchlist, watchlist_id)
    if watchlist is None:
        raise WatchlistNotFoundError

    statement = (
        select(WatchlistItem)
        .join(Stock, WatchlistItem.stock_id == Stock.id)
        .where(
            WatchlistItem.watchlist_id == watchlist_id,
            Stock.symbol == symbol,
        )
    )
    item = session.scalar(statement)
    if item is None:
        raise StockNotInWatchlistError

    session.delete(item)
    session.commit()
