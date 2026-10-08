import json

import httpx


def test_demo_defaults_to_offline_even_when_environment_selects_qwen(
    stock_session, monkeypatch, tmp_path, capsys
) -> None:
    from app import tool_calling_demo

    monkeypatch.setenv("MODEL_PROVIDER", "qwen")
    monkeypatch.chdir(tmp_path)
    original_client = httpx.Client

    def unexpected_request(request: httpx.Request) -> httpx.Response:
        raise AssertionError("默认演示不应发出网络请求")

    monkeypatch.setattr(
        tool_calling_demo.httpx,
        "Client",
        lambda: original_client(transport=httpx.MockTransport(unexpected_request)),
    )

    tool_calling_demo.main([])

    output = capsys.readouterr().out
    assert "离线假模型演示" in output
    log_path = tmp_path / "data/private/day10-tool-calls.jsonl"
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert [record["tool_call_id"] for record in records] == ["offline_valid", "offline_rejected"]
    assert records[0]["result"] == {"change_percent": "-10.0000"}
    assert records[1]["error"]["kind"] == "invalid_arguments"


def test_demo_explicit_qwen_uses_one_native_request_and_logs_python_result(
    stock_session, monkeypatch, tmp_path, capsys
) -> None:
    from app import tool_calling_demo
    from app.tools.registry import tool_definitions

    monkeypatch.setenv("MODEL_PROVIDER", "fake")
    monkeypatch.setenv("MODEL_NAME", "qwen-plus")
    monkeypatch.setenv("MODEL_BASE_URL", "https://example.test/compatible-mode/v1")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-only-key")
    monkeypatch.chdir(tmp_path)
    original_client = httpx.Client
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append(payload)
        assert str(request.url) == "https://example.test/compatible-mode/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-only-key"
        assert payload["tools"] == tool_definitions()
        assert payload["tool_choice"] == "auto"
        assert "10" in payload["messages"][-1]["content"]
        assert "9" in payload["messages"][-1]["content"]
        assert "0 到 9" not in payload["messages"][-1]["content"]
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "call_provider_test",
                                    "type": "function",
                                    "function": {
                                        "name": "calculate_change",
                                        "arguments": '{"previous_close": 10, "current_close": 9}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            },
        )

    monkeypatch.setattr(
        tool_calling_demo.httpx,
        "Client",
        lambda: original_client(transport=httpx.MockTransport(respond)),
    )

    tool_calling_demo.main(["--provider", "qwen"])

    assert len(requests) == 1
    output = capsys.readouterr().out
    assert "千问工具选择演示" in output
    assert "test-only-key" not in output
    log_path = tmp_path / "data/private/day10-tool-calls.jsonl"
    records = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 1
    assert records[0]["tool_call_id"] == "call_provider_test"
    assert records[0]["status"] == "success"
    assert records[0]["result"] == {"change_percent": "-10.0000"}
