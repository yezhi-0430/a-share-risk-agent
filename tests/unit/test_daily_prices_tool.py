from datetime import date, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy import select


def make_arguments(**overrides):
    from app.tools import market_data

    payload = {
        "stock_code": "000001.SZ",
        "start_date": "2026-09-10",
        "end_date": "2026-09-20",
    }
    payload.update(overrides)
    return market_data.DailyPricesArguments.model_validate(payload)


def add_price(session, stock_code: str, trade_date: date, price: str = "10.25") -> None:
    from app.database import DailyPrice, Stock

    stock = session.scalar(select(Stock).where(Stock.symbol == stock_code))
    session.add(
        DailyPrice(
            stock_id=stock.id,
            trade_date=trade_date,
            open=Decimal(price),
            high=Decimal(price) + Decimal("1"),
            low=Decimal(price) - Decimal("1"),
            close=Decimal(price),
            volume=100,
        )
    )
    session.commit()


def test_filters_dates_and_stock_with_latest_first(stock_session) -> None:
    from app.tools import market_data

    for day in (1, 10, 11, 20, 30):
        add_price(stock_session, "000001.SZ", date(2026, 9, day))
    add_price(stock_session, "600000.SH", date(2026, 9, 15), price="20")

    result = market_data.get_daily_prices(make_arguments(), stock_session)

    assert [row["trade_date"] for row in result] == [
        "2026-09-20",
        "2026-09-11",
        "2026-09-10",
    ]
    assert result[0] == {
        "trade_date": "2026-09-20",
        "open": "10.2500",
        "high": "11.2500",
        "low": "9.2500",
        "close": "10.2500",
        "volume": 100,
    }


def test_known_stock_without_prices_returns_empty_list(stock_session) -> None:
    from app.tools import market_data

    assert market_data.get_daily_prices(make_arguments(), stock_session) == []


def test_prices_outside_range_return_empty_list(stock_session) -> None:
    from app.tools import market_data

    add_price(stock_session, "000001.SZ", date(2026, 9, 1))

    assert market_data.get_daily_prices(make_arguments(), stock_session) == []


def test_supports_single_day_range(stock_session) -> None:
    from app.tools import market_data

    add_price(stock_session, "000001.SZ", date(2026, 9, 10))
    add_price(stock_session, "000001.SZ", date(2026, 9, 11))

    result = market_data.get_daily_prices(make_arguments(end_date="2026-09-10"), stock_session)

    assert [row["trade_date"] for row in result] == ["2026-09-10"]


def test_unknown_stock_raises_instead_of_returning_empty_list(stock_session) -> None:
    from app.tools import market_data

    arguments = make_arguments(stock_code="999999.SH")

    with pytest.raises(market_data.StockNotFoundError, match="股票不存在"):
        market_data.get_daily_prices(arguments, stock_session)


def test_parses_iso_dates(stock_session) -> None:
    arguments = make_arguments()

    assert arguments.start_date == date(2026, 9, 10)
    assert arguments.end_date == date(2026, 9, 20)


@pytest.mark.parametrize(
    "overrides",
    [
        {"start_date": "2026-09-21"},
        {"start_date": "2026-02-30"},
        {"end_date": "2026-09-31"},
        {"start_date": ""},
        {"end_date": None},
        {"start_date": 0},
        {"end_date": True},
        {"start_date": "2026-09-10T00:00:00"},
        {"start_date": datetime(2026, 9, 10)},
        {"start_date": "20260910"},
        {"stock_code": 1},
        {"limit": 5},
    ],
)
def test_rejects_invalid_daily_price_arguments(stock_session, overrides) -> None:
    with pytest.raises(ValidationError):
        make_arguments(**overrides)


@pytest.mark.parametrize("missing", ["stock_code", "start_date", "end_date"])
def test_requires_all_query_parameters(stock_session, missing: str) -> None:
    from app.tools import market_data

    payload = {
        "stock_code": "000001.SZ",
        "start_date": "2026-09-10",
        "end_date": "2026-09-20",
    }
    payload.pop(missing)

    with pytest.raises(ValidationError):
        market_data.DailyPricesArguments.model_validate(payload)
