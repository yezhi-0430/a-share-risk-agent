import argparse
import logging
from pathlib import Path

import httpx

from app.config import Settings
from app.llm_client import create_model_client
from app.llm_types import ToolReply
from app.tool_calling import run_tool_turn


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Day 10 单轮工具调用演示")
    parser.add_argument(
        "--provider",
        choices=("fake", "qwen"),
        default="fake",
        help="默认 fake 离线演示；qwen 使用本地配置发出真实模型请求",
    )
    args = parser.parse_args(argv)
    settings = Settings().model_copy(update={"model_provider": args.provider})
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
        if args.provider == "fake":
            messages = [{"role": "user", "content": "分别计算 10 到 9、0 到 9 的涨跌幅。"}]
            label = "离线假模型演示（调用请求预先配置）"
        else:
            messages = [
                {
                    "role": "system",
                    "content": "根据用户提供的数据选择合适的工具。金融涨跌幅交给计算工具计算。",
                },
                {
                    "role": "user",
                    "content": "虚构数据：昨日收盘价 10 元，今日收盘价 9 元，请计算涨跌幅。",
                },
            ]
            label = f"千问工具选择演示（{settings.model_name}）"
        with httpx.Client() as http_client:
            client = create_model_client(settings, http_client, fake_tool_reply=reply)
            turn = run_tool_turn(client, messages)
        print(label)
        print(turn.model_dump_json(indent=2))
        print(f"Log: {log_path}")
    finally:
        logger.removeHandler(handler)
        handler.close()
        logger.setLevel(previous_level)
        logger.propagate = previous_propagate


if __name__ == "__main__":
    main()
