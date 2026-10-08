from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.tools import calculations


@pytest.mark.parametrize(
    ("previous_close", "current_close", "expected"),
    [
        (10, 9, "-10.0000"),
        (10, 11, "10.0000"),
        (10, 10, "0.0000"),
        (0.1, 0.3, "200.0000"),
        ("3", "4", "33.3333"),
        ("128", "129", "0.7813"),
        ("128", "127", "-0.7813"),
        ("0.0001", "99999999999999.9999", "99999999999999999800.0000"),
    ],
)
def test_calculates_change_percent(previous_close, current_close, expected: str) -> None:
    arguments = calculations.CalculateChangeArguments.model_validate(
        {"previous_close": previous_close, "current_close": current_close}
    )

    result = calculations.calculate_change(arguments)

    assert result == {"change_percent": expected}


def test_validates_prices_as_decimal() -> None:
    arguments = calculations.CalculateChangeArguments.model_validate(
        {"previous_close": 0.1, "current_close": "0.3000"}
    )

    assert arguments.previous_close == Decimal("0.1")
    assert arguments.current_close == Decimal("0.3000")


@pytest.mark.parametrize(
    "arguments",
    [
        {"previous_close": 0, "current_close": 9},
        {"previous_close": -10, "current_close": 9},
        {"previous_close": 10, "current_close": 0},
        {"previous_close": 10, "current_close": -9},
        {"previous_close": "随便", "current_close": 9},
        {"previous_close": 10, "current_close": "随便"},
        {"previous_close": True, "current_close": 9},
        {"previous_close": 10, "current_close": False},
        {"previous_close": None, "current_close": 9},
        {"previous_close": 10, "current_close": None},
        {"previous_close": [], "current_close": 9},
        {"previous_close": "NaN", "current_close": 9},
        {"previous_close": "Infinity", "current_close": 9},
        {"previous_close": 10, "current_close": "NaN"},
        {"previous_close": 10, "current_close": float("inf")},
        {"previous_close": "10.00001", "current_close": 9},
        {"previous_close": 10, "current_close": "9.00001"},
        {"previous_close": "100000000000000", "current_close": 9},
        {"previous_close": 10, "current_close": "100000000000000"},
        {"current_close": 9},
        {"previous_close": 10},
        {"previous_close": 10, "current_close": 9, "risk_level": "low"},
    ],
)
def test_rejects_invalid_calculation_arguments(arguments: dict[str, object]) -> None:
    with pytest.raises(ValidationError):
        calculations.CalculateChangeArguments.model_validate(arguments)
