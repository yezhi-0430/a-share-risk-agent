from app.stocks.models import StockSummary


class StockCatalog:
    def __init__(self, stocks: tuple[StockSummary, ...]) -> None:
        self._stocks = stocks

    def search(self, query: str) -> list[StockSummary]:
        normalized = query.strip().upper()
        return [
            stock
            for stock in self._stocks
            if normalized in stock.symbol.upper() or normalized in stock.name.upper()
        ]

    def get(self, symbol: str) -> StockSummary | None:
        normalized = symbol.strip().upper()
        return next((stock for stock in self._stocks if stock.symbol == normalized), None)


def create_demo_catalog() -> StockCatalog:
    return StockCatalog(
        (
            StockSummary(symbol="000001.SZ", name="平安银行", market="SZ"),
            StockSummary(symbol="300750.SZ", name="宁德时代", market="SZ"),
            StockSummary(symbol="600519.SH", name="贵州茅台", market="SH"),
            StockSummary(symbol="601318.SH", name="中国平安", market="SH"),
            StockSummary(symbol="688981.SH", name="中芯国际", market="SH"),
        )
    )

