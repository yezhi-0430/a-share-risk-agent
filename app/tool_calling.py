from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.llm_client import ModelClient
from app.llm_types import ToolReply
from app.tools.executor import ToolExecutionRecord, execute_tool
from app.tools.registry import tool_definitions


class ToolTurnResult(BaseModel):
    reply: ToolReply
    executions: list[ToolExecutionRecord]


def run_tool_turn(
    client: ModelClient,
    messages: list[dict[str, str]],
    session: Session | None = None,
) -> ToolTurnResult:
    reply = client.chat_with_tools(messages, tool_definitions())
    executions = []
    for call in reply.tool_calls:
        record = execute_tool(
            call.function.name,
            call.function.arguments,
            session=session,
            tool_call_id=call.id,
        )
        executions.append(record)
    return ToolTurnResult(reply=reply, executions=executions)
