"""Run a bounded model/tool loop using the existing validated executor."""

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.llm_client import ModelClient
from app.tool_calling import run_tool_turn
from app.tool_messages import require_answer_or_calls, tool_result_messages
from app.tools.executor import ToolExecutionRecord


class AgentLoopResult(BaseModel):
    status: Literal["completed", "max_rounds_exceeded"]
    answer: str | None
    rounds: int = Field(ge=1)
    executions: list[ToolExecutionRecord]


def run_agent_loop(
    client: ModelClient,
    messages: Sequence[Mapping[str, object]],
    session: Session | None = None,
    *,
    max_rounds: int = 5,
) -> AgentLoopResult:
    """Count model requests, execute calls, and stop on an answer or the round limit."""
    if type(max_rounds) is not int or max_rounds < 1:
        raise ValueError("max_rounds 必须为正整数")

    history: list[dict[str, object]] = deepcopy([dict(message) for message in messages])
    executions: list[ToolExecutionRecord] = []
    for round_number in range(1, max_rounds + 1):
        turn = run_tool_turn(client, history, session)
        executions.extend(turn.executions)
        require_answer_or_calls(turn.reply)
        if not turn.reply.tool_calls:
            return AgentLoopResult(
                status="completed",
                answer=turn.reply.content,
                rounds=round_number,
                executions=executions,
            )
        history.extend(tool_result_messages(turn))

    return AgentLoopResult(
        status="max_rounds_exceeded",
        answer=None,
        rounds=max_rounds,
        executions=executions,
    )
