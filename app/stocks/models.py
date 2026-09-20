from typing import Literal

from pydantic import BaseModel


class StockSummary(BaseModel):
    symbol: str
    name: str
    market: Literal["SH", "SZ", "BJ"]

