from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Watchlist


def create_watchlist(session: Session, name: str) -> Watchlist:
    watchlist = Watchlist(name=name)
    session.add(watchlist)
    session.commit()
    session.refresh(watchlist)
    return watchlist


def get_watchlists(session: Session) -> list[Watchlist]:
    statement = select(Watchlist).order_by(Watchlist.id)
    return list(session.scalars(statement).all())
