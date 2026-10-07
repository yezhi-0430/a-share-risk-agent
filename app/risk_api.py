from collections.abc import Iterator
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import Settings
from app.llm_client import ModelClient, create_model_client
from app.risk_summary import (
    RiskSummary,
    RiskSummaryParseError,
    generate_risk_summary,
)

router = APIRouter()


class RiskSummaryRequest(BaseModel):
    input_text: str = Field(min_length=1)


def get_model_client() -> Iterator[ModelClient]:
    with httpx.Client() as http_client:
        yield create_model_client(Settings(), http_client)


@router.post("/api/v1/risk-summary", response_model=RiskSummary)
def create_risk_summary(
    payload: RiskSummaryRequest,
    model: Annotated[ModelClient, Depends(get_model_client)],
) -> RiskSummary:
    try:
        return generate_risk_summary(model, payload.input_text)
    except RiskSummaryParseError as exc:
        raise HTTPException(
            status_code=502,
            detail="模型输出格式无效",
        ) from exc
