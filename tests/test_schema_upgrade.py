from datetime import date

import pytest
from sqlalchemy import BigInteger, inspect, select, text

from app import schema_upgrade
from app.database import DailyPrice, SessionLocal, Stock, Watchlist, WatchlistItem, engine


def test_upgrade_preserves_existing_records_and_is_idempotent():
    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE daily_prices ALTER COLUMN volume TYPE INTEGER"))
    with SessionLocal() as session:
        stock = Stock(symbol="000001.sz", name="保留名称")
        group = Watchlist(name="保留自选组")
        session.add_all([stock, group])
        session.flush()
        stock_id, group_id = stock.id, group.id
        session.add(WatchlistItem(stock_id=stock_id, watchlist_id=group_id))
        session.add(
            DailyPrice(
                stock_id=stock_id,
                trade_date=date(2026, 9, 25),
                open="10",
                high="11",
                low="9",
                close="10",
                volume=100,
            )
        )
        session.commit()
    schema_upgrade.upgrade_database(engine)
    schema_upgrade.upgrade_database(engine)
    column = next(
        item for item in inspect(engine).get_columns("daily_prices") if item["name"] == "volume"
    )
    assert isinstance(column["type"], BigInteger)
    with SessionLocal() as session:
        stock = session.get(Stock, stock_id)
        assert stock.symbol == "000001.SZ"
        assert stock.name == "保留名称"
        assert session.scalar(select(WatchlistItem)).watchlist_id == group_id
        assert session.scalar(select(DailyPrice)).volume == 100


def test_upgrade_reports_case_collisions_without_merging_records():
    with SessionLocal() as session:
        session.add_all(
            [
                Stock(symbol="000001.sz", name="甲"),
                Stock(symbol="000001.SZ", name="乙"),
            ]
        )
        session.commit()
    with pytest.raises(ValueError, match="股票代码归一化冲突"):
        schema_upgrade.upgrade_database(engine)
    with SessionLocal() as session:
        assert set(session.scalars(select(Stock.symbol))) == {"000001.sz", "000001.SZ"}
