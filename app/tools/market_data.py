from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Stock


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


def get_stock_profile(
    arguments: StockProfileArguments,
    session: Session,
) -> dict[str, str]:
    stock = session.scalar(select(Stock).where(Stock.symbol == arguments.stock_code))

    if stock is None:
        raise StockNotFoundError("股票不存在")

    return {"stock_code": stock.symbol, "name": stock.name}
