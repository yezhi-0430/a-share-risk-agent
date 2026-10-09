"""Day 11 first step: execute one tool turn, then request model feedback once."""

import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Literal

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.llm_client import ModelClient, ModelResponseError
from app.llm_types import ToolReply
from app.tool_calling import run_tool_turn
from app.tools.executor import ToolExecutionRecord
from app.tools.registry import tool_definitions


class ToolFeedbackResult(BaseModel):
    status: Literal["completed", "needs_tools"]
    rounds: Literal[1, 2]
    reply: ToolReply
    executions: list[ToolExecutionRecord]


def _require_answer_or_calls(reply: ToolReply) -> None:
    if not reply.tool_calls and (reply.content is None or not reply.content.strip()):
        raise ModelResponseError("模型未返回有效内容")


def run_tool_feedback(
    client: ModelClient,
    messages: Sequence[Mapping[str, object]],
    session: Session | None = None,
) -> ToolFeedbackResult:
    """Return a final answer or pending calls; never execute the second turn's calls."""
    history: list[dict[str, object]] = deepcopy([dict(message) for message in messages])
    turn = run_tool_turn(client, history, session)
    _require_answer_or_calls(turn.reply)
    if not turn.reply.tool_calls:
        return ToolFeedbackResult(status="completed", rounds=1, reply=turn.reply, executions=[])

    history.append({"role": "assistant", **turn.reply.model_dump()})
    for record in turn.executions:
        payload = {
            "status": record.status,
            "result": record.result,
            "error": record.error.model_dump(exclude={"details"}) if record.error else None,
        }
        history.append(
            {
                "role": "tool",
                "tool_call_id": record.tool_call_id,
                "content": json.dumps(payload, ensure_ascii=False),
            }
        )

    reply = client.chat_with_tools(history, tool_definitions())
    _require_answer_or_calls(reply)
    return ToolFeedbackResult(
        status="needs_tools" if reply.tool_calls else "completed",
        rounds=2,
        reply=reply,
        executions=turn.executions,
    )
