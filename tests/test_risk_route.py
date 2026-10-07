from app.llm_client import FakeModelClient
from app.main import app
from app.risk_api import get_model_client


def test_main_app_includes_risk_summary_route(client, monkeypatch) -> None:
    monkeypatch.setitem(
        app.dependency_overrides,
        get_model_client,
        lambda: FakeModelClient(reply="不是JSON"),
    )

    response = client.post(
        "/api/v1/risk-summary",
        json={"input_text": "用户提供：今日收盘价9元"},
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "模型输出格式无效"}
