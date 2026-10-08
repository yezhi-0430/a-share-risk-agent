import logging
from pathlib import Path

from app.llm_client import FakeModelClient
from app.llm_types import ToolReply
from app.tool_calling import run_tool_turn


def main() -> None:
    log_path = Path("data/private/day10-tool-calls.jsonl").resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("app.tools.executor")
    previous_level, previous_propagate = logger.level, logger.propagate
    logger.setLevel(logging.INFO)
    logger.propagate = False
    logger.addHandler(handler)

    try:
        reply = ToolReply.model_validate(
            {
                "content": None,
                "tool_calls": [
                    {
                        "id": call_id,
                        "type": "function",
                        "function": {
                            "name": "calculate_change",
                            "arguments": arguments,
                        },
                    }
                    for call_id, arguments in (
                        ("offline_valid", '{"previous_close": 10, "current_close": 9}'),
                        ("offline_rejected", '{"previous_close": 0, "current_close": 9}'),
                    )
                ],
            }
        )
        client = FakeModelClient("离线演示", tool_reply=reply)
        turn = run_tool_turn(
            client,
            [{"role": "user", "content": "分别计算 10 到 9、0 到 9 的涨跌幅。"}],
        )
        print("离线假模型演示（调用请求预先配置）")
        print(turn.model_dump_json(indent=2))
        print(f"Log: {log_path}")
    finally:
        logger.removeHandler(handler)
        handler.close()
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate


if __name__ == "__main__":
    main()
