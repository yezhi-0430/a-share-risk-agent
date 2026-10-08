from datetime import date
from re import fullmatch
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator, model_validator
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import DailyPrice, Stock


class StockNotFoundError(Exception):
    pass


class StockProfileArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    stock_code: Annotated[
        str,
        StringConstraints(
            strict=True,
            strip_whitespace=True,
            pattern=r"^[0-9]{6}(?:\.(?:SH|SZ|BJ))?$",
        ),
    ]


class DailyPricesArguments(StockProfileArguments):
    start_date: date
    end_date: date

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_date(cls, value: object) -> date:
        if type(value) is date:
            return value
        if isinstance(value, str) and fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            return date.fromisoformat(value)
        raise ValueError("日期必须使用 YYYY-MM-DD 格式")

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.start_date > self.end_date:
            raise ValueError("开始日期不能晚于结束日期")
        return self


def get_stock_profile(
    arguments: StockProfileArguments,
    session: Session,
) -> dict[str, str]:
    stock = session.scalar(select(Stock).where(Stock.symbol == arguments.stock_code))

    if stock is None:
        raise StockNotFoundError("股票不存在")

    return {"stock_code": stock.symbol, "name": stock.name}


def get_daily_prices(
    arguments: DailyPricesArguments,
    session: Session,
) -> list[dict[str, object]]:
    stock = session.scalar(select(Stock).where(Stock.symbol == arguments.stock_code))

    if stock is None:
        raise StockNotFoundError("股票不存在")

    prices = session.scalars(
        select(DailyPrice)
        .where(
            DailyPrice.stock_id == stock.id,
            DailyPrice.trade_date >= arguments.start_date,
            DailyPrice.trade_date <= arguments.end_date,
        )
        .order_by(DailyPrice.trade_date.desc())
    ).all()

    return [
        {
            "trade_date": item.trade_date.isoformat(),
            "open": str(item.open),
            "high": str(item.high),
            "low": str(item.low),
            "close": str(item.close),
            "volume": item.volume,
        }
        for item in prices
    ]
