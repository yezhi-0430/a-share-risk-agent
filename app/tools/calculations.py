from decimal import ROUND_HALF_UP, Decimal

from pydantic import BaseModel, ConfigDict, Field


class CalculateChangeArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")

    previous_close: Decimal = Field(gt=0, allow_inf_nan=False, max_digits=18, decimal_places=4)
    current_close: Decimal = Field(gt=0, allow_inf_nan=False, max_digits=18, decimal_places=4)


def calculate_change(arguments: CalculateChangeArguments) -> dict[str, str]:
    change_percent = (
        (arguments.current_close - arguments.previous_close)
        / arguments.previous_close
        * Decimal("100")
    )
    rounded = change_percent.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return {"change_percent": str(rounded)}
