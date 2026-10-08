from pydantic import BaseModel

from app.tools.calculations import CalculateChangeArguments
from app.tools.market_data import DailyPricesArguments, StockProfileArguments

TOOL_ARGUMENT_MODELS: dict[str, type[BaseModel]] = {
    "get_stock_profile": StockProfileArguments,
    "get_daily_prices": DailyPricesArguments,
    "calculate_change": CalculateChangeArguments,
}

TOOL_DESCRIPTIONS = {
    "get_stock_profile": "按库中完整股票代码查询本地保存的股票代码和名称，不补造资料。",
    "get_daily_prices": (
        "按库中完整股票代码和 YYYY-MM-DD 日期闭区间查询本地日线，最新日期在前。"
        "开始日期不能晚于结束日期，空列表表示范围内没有数据。"
    ),
    "calculate_change": (
        "用 Python 计算两个正价格之间的涨跌幅百分数，保留四位小数；结果 -10.0000 表示下跌 10%。"
    ),
}


def tool_definitions() -> list[dict[str, object]]:
    return [
        {
            "type": "function",
            "function": {
                "name": name,
                "description": TOOL_DESCRIPTIONS[name],
                "parameters": model.model_json_schema(),
            },
        }
        for name, model in TOOL_ARGUMENT_MODELS.items()
    ]
