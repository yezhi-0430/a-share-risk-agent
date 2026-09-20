from typing import Annotated

from pydantic import BaseModel, StringConstraints, field_validator

from app.stocks.models import StockSummary

WatchlistName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=40),
]
StockSymbol = Annotated[str, StringConstraints(pattern=r"^\d{6}\.(SH|SZ|BJ)$")]


class CreateWatchlistRequest(BaseModel):
    name: WatchlistName


class UpdateWatchlistRequest(BaseModel):
    name: WatchlistName


class AddWatchlistItemRequest(BaseModel):
    symbol: StockSymbol

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, value: object) -> object:
        return value.strip().upper() if isinstance(value, str) else value


class Watchlist(BaseModel):
    id: int
    name: str
    items: list[StockSummary]
