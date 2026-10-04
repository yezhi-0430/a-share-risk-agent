from sqlalchemy import Integer, Numeric, UniqueConstraint

from app.database import Base


def test_defines_watchlists_table() -> None:
    assert "watchlists" in Base.metadata.tables


def test_watchlists_table_has_name_column() -> None:
    table = Base.metadata.tables["watchlists"]

    assert "name" in table.columns


def test_watchlists_name_has_max_length_40() -> None:
    table = Base.metadata.tables["watchlists"]

    assert table.columns["name"].type.length == 40


def test_defines_stocks_table() -> None:
    assert "stocks" in Base.metadata.tables


def test_stocks_table_has_required_columns() -> None:
    table = Base.metadata.tables["stocks"]

    assert set(table.columns.keys()) == {"id", "symbol", "name"}


def test_stock_symbol_is_unique() -> None:
    table = Base.metadata.tables["stocks"]

    assert table.columns["symbol"].unique is True


def test_defines_watchlist_items_table() -> None:
    assert "watchlist_items" in Base.metadata.tables


def test_watchlist_items_has_required_columns() -> None:
    table = Base.metadata.tables["watchlist_items"]

    assert set(table.columns.keys()) == {
        "id",
        "watchlist_id",
        "stock_id",
    }


def test_watchlist_items_has_foreign_keys() -> None:
    table = Base.metadata.tables["watchlist_items"]
    targets = {foreign_key.target_fullname for foreign_key in table.foreign_keys}

    assert targets == {"watchlists.id", "stocks.id"}


def test_watchlist_item_is_unique_within_watchlist() -> None:
    table = Base.metadata.tables["watchlist_items"]
    unique_column_sets = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("watchlist_id", "stock_id") in unique_column_sets


def test_daily_prices_have_required_columns() -> None:
    table = Base.metadata.tables["daily_prices"]

    assert set(table.columns.keys()) == {
        "id",
        "stock_id",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

def test_daily_price_is_unique_per_stock_and_date() -> None:
    table = Base.metadata.tables["daily_prices"]

    unique_column_sets = {
        tuple(column.name for column in constraint.columns)
        for constraint in table.constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert ("stock_id", "trade_date") in unique_column_sets


def test_daily_price_has_stock_foreign_key() -> None:
    table = Base.metadata.tables["daily_prices"]

    targets = {
        foreign_key.target_fullname
        for foreign_key in table.foreign_keys
    }

    assert targets == {"stocks.id"}


def test_daily_price_uses_numeric_for_prices() -> None:
    table = Base.metadata.tables["daily_prices"]

    for column_name in ("open", "high", "low", "close"):
        assert isinstance(table.columns[column_name].type, Numeric)


def test_daily_price_uses_integer_for_volume() -> None:
    table = Base.metadata.tables["daily_prices"]

    assert isinstance(table.columns["volume"].type, Integer)
