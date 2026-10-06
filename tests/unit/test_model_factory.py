import json

import httpx
import pytest

from app.config import Settings
from app.llm_client import ModelConfigurationError, create_model_client


def make_settings(**model_values: object) -> Settings:
    return Settings(
        _env_file=None,
        database_host="localhost",
        database_port=5432,
        database_name="test_db",
        database_user="test_user",
        database_password="test-password",
        **model_values,
    )


def test_factory_uses_fake_model_without_api_key() -> None:
    settings = make_settings(model_provider="fake")

    def unexpected_request(request: httpx.Request) -> httpx.Response:
        raise AssertionError("假模型不应发送 HTTP 请求")

    with httpx.Client(transport=httpx.MockTransport(unexpected_request)) as http_client:
        model = create_model_client(settings, http_client, fake_reply="离线回答")
        reply = model.chat([{"role": "user", "content": "你好"}])

    assert reply == "离线回答"


def test_factory_uses_configured_qwen_endpoint_and_model() -> None:
    settings = make_settings(
        model_provider="qwen",
        model_name="qwen-plus",
        model_base_url="https://example.test/compatible-mode/v1",
        dashscope_api_key="test-only-key",
    )

    def respond(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://example.test/compatible-mode/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-only-key"
        assert json.loads(request.content)["model"] == "qwen-plus"
        return httpx.Response(200, json={"choices": [{"message": {"content": "在线回答"}}]})

    with httpx.Client(transport=httpx.MockTransport(respond)) as http_client:
        model = create_model_client(settings, http_client)
        reply = model.chat([{"role": "user", "content": "你好"}])

    assert reply == "在线回答"


def test_factory_requires_key_for_qwen() -> None:
    settings = make_settings(model_provider="qwen", dashscope_api_key=None)
    with httpx.Client() as http_client:
        with pytest.raises(ModelConfigurationError):
            create_model_client(settings, http_client)
