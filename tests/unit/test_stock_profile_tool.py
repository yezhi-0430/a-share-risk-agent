import pytest
from pydantic import ValidationError


@pytest.mark.parametrize(
    ("stock_code", "name"),
    [("000001.SZ", "本地保存的名称甲"), ("600000.SH", "本地保存的名称乙")],
)
def test_returns_stored_stock_profile(stock_session, stock_code: str, name: str) -> None:
    from app.tools import market_data

    arguments = market_data.StockProfileArguments.model_validate({"stock_code": stock_code})

    result = market_data.get_stock_profile(arguments, stock_session)

    assert result == {"stock_code": stock_code, "name": name}


@pytest.mark.parametrize("stock_code", ["999999.SH", "000001"])
def test_reports_unknown_stock(stock_session, stock_code: str) -> None:
    from app.tools import market_data

    arguments = market_data.StockProfileArguments.model_validate({"stock_code": stock_code})

    with pytest.raises(market_data.StockNotFoundError, match="股票不存在"):
        market_data.get_stock_profile(arguments, stock_session)


def test_strips_whitespace_from_stock_code(stock_session) -> None:
    from app.tools import market_data

    arguments = market_data.StockProfileArguments.model_validate({"stock_code": " 000001.SZ "})

    assert arguments.stock_code == "000001.SZ"
    assert market_data.get_stock_profile(arguments, stock_session)["name"] == "本地保存的名称甲"


@pytest.mark.parametrize(
    "arguments",
    [
        {},
        {"stock_code": 1},
        {"stock_code": True},
        {"stock_code": None},
        {"stock_code": ""},
        {"stock_code": "   "},
        {"stock_code": "00001.SZ"},
        {"stock_code": "000001.XX"},
        {"stock_code": "000001.sz"},
        {"stock_code": "０００００１.SZ"},
        {"stock_code": "000001.SZ' OR '1'='1"},
        {"stock_code": "000001.SZ", "name": "额外参数"},
    ],
)
def test_rejects_invalid_profile_arguments(stock_session, arguments: dict[str, object]) -> None:
    from app.tools import market_data

    with pytest.raises(ValidationError):
        market_data.StockProfileArguments.model_validate(arguments)
