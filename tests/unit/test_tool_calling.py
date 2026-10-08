import json
import logging

import httpx
import pytest

from app import tool_calling
from app.llm_client import FakeModelClient, ModelTimeoutError, QwenModelClient
from app.llm_types import ToolReply

MESSAGES = [{"role": "user", "content": "昨日 10 元，今日 9 元，计算涨跌幅。"}]
VALID_PRICES = '{"previous_close": 10, "current_close": 9}'


def tool_reply(*calls: tuple[str, str, str]) -> ToolReply:
    return ToolReply.model_validate(
        {
            "content": None,
            "tool_calls": [
                {
                    "id": call_id,
                    "type": "function",
                    "function": {"name": name, "arguments": arguments},
                }
                for call_id, name, arguments in calls
            ],
        }
    )


def test_native_model_request_executes_and_logs_correlated_calculation(
    stock_session, caplog
) -> None:
    from app.tools.registry import tool_definitions

    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        requests.append(payload)
        assert payload["messages"] == MESSAGES
        assert payload["tools"] == tool_definitions()
        assert payload["tool_choice"] == "auto"
        reply = tool_reply(("call_calc_1", "calculate_change", VALID_PRICES))
        return httpx.Response(200, json={"choices": [{"message": reply.model_dump()}]})

    with httpx.Client(transport=httpx.MockTransport(respond)) as http_client:
        with caplog.at_level(logging.INFO, logger="app.tools.executor"):
            turn = tool_calling.run_tool_turn(
                QwenModelClient("test-only-key", http_client), MESSAGES
            )

    assert len(requests) == 1
    assert turn.reply.content is None
    assert len(turn.executions) == 1
    record = turn.executions[0]
    assert record.tool_call_id == "call_calc_1"
    assert record.tool_name == "calculate_change"
    assert record.arguments == VALID_PRICES
    assert record.status == "success"
    assert record.result == {"change_percent": "-10.0000"}
    logs = [
        json.loads(item.message) for item in caplog.records if item.name == "app.tools.executor"
    ]
    assert logs == [record.model_dump(mode="json")]


@pytest.mark.parametrize("arguments", ['{"previous_close": 0, "current_close": 9}', "{broken"])
def test_model_bad_arguments_are_recorded_without_calculation(
    stock_session, monkeypatch, arguments
):
    from app.tools import executor

    calls = []
    monkeypatch.setattr(executor, "calculate_change", lambda value: calls.append(value))
    model = FakeModelClient("unused", tool_reply(("call_bad", "calculate_change", arguments)))

    turn = tool_calling.run_tool_turn(model, MESSAGES)

    assert calls == []
    record = turn.executions[0]
    assert record.tool_call_id == "call_bad"
    assert record.arguments == arguments
    assert record.status == "error"
    assert record.result is None
    assert record.error.kind == "invalid_arguments"


def test_model_unknown_name_cannot_open_database(stock_session, monkeypatch) -> None:
    from app.tools import executor

    opened = []
    monkeypatch.setattr(executor, "SessionLocal", lambda: opened.append(True))
    model = FakeModelClient("unused", tool_reply(("call_unknown", "delete_stock", "{}")))

    turn = tool_calling.run_tool_turn(model, MESSAGES)

    assert opened == []
    assert turn.executions[0].tool_call_id == "call_unknown"
    assert turn.executions[0].error.kind == "unknown_tool"


def test_model_profile_call_uses_supplied_session(stock_session) -> None:
    model = FakeModelClient(
        "unused", tool_reply(("call_profile", "get_stock_profile", '{"stock_code": "000001.SZ"}'))
    )

    turn = tool_calling.run_tool_turn(model, MESSAGES, session=stock_session)

    assert turn.executions[0].status == "success"
    assert turn.executions[0].result == {"stock_code": "000001.SZ", "name": "本地保存的名称甲"}


def test_text_reply_does_not_execute_any_tool(stock_session, monkeypatch) -> None:
    executed = []
    monkeypatch.setattr(tool_calling, "execute_tool", lambda *args, **kwargs: executed.append(True))

    turn = tool_calling.run_tool_turn(FakeModelClient("请提供两个价格"), MESSAGES)

    assert turn.reply.content == "请提供两个价格"
    assert turn.reply.tool_calls == []
    assert turn.executions == []
    assert executed == []


def test_multiple_requests_keep_order_and_continue_after_rejection(stock_session) -> None:
    model = FakeModelClient(
        "unused",
        tool_reply(
            ("call_bad", "calculate_change", '{"previous_close": 0, "current_close": 9}'),
            ("call_good", "calculate_change", VALID_PRICES),
        ),
    )

    turn = tool_calling.run_tool_turn(model, MESSAGES)

    assert [record.tool_call_id for record in turn.executions] == ["call_bad", "call_good"]
    assert [record.status for record in turn.executions] == ["error", "success"]
    assert turn.executions[1].result == {"change_percent": "-10.0000"}


def test_model_failure_does_not_start_tool_execution(stock_session, monkeypatch) -> None:
    executed = []
    monkeypatch.setattr(tool_calling, "execute_tool", lambda *args, **kwargs: executed.append(True))

    def respond(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("模拟超时", request=request)

    with httpx.Client(transport=httpx.MockTransport(respond)) as http_client:
        with pytest.raises(ModelTimeoutError):
            tool_calling.run_tool_turn(QwenModelClient("test-only-key", http_client), MESSAGES)
    assert executed == []
