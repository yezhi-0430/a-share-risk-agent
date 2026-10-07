import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.llm_client import FakeModelClient
from app.risk_api import get_model_client, router


def test_returns_502_for_invalid_model_reply() -> None:
    application = FastAPI()
    application.include_router(router)
    application.dependency_overrides[get_model_client] = lambda: FakeModelClient(reply="不是JSON")

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/risk-summary",
            json={"input_text": "用户提供：今日收盘价9元"},
        )

    assert response.status_code == 502
    assert response.json() == {"detail": "模型输出格式无效"}


def test_returns_valid_risk_summary() -> None:
    expected = {
        "facts": ["今日收盘价9元"],
        "inferences": [],
        "unknowns": ["缺少成交量"],
        "risk_level": "unknown",
        "sources": ["用户提供的数据"],
    }

    application = FastAPI()
    application.include_router(router)
    application.dependency_overrides[get_model_client] = lambda: FakeModelClient(
        reply=json.dumps(expected, ensure_ascii=False)
    )

    with TestClient(application) as client:
        response = client.post(
            "/api/v1/risk-summary",
            json={"input_text": "用户提供：今日收盘价9元"},
        )

    assert response.status_code == 200
    assert response.json() == expected
