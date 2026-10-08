import logging
from pathlib import Path

from app.tools.executor import execute_tool


def main() -> None:
    log_path = Path("data/private/day10-tool-calls.jsonl").resolve()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_path,
        encoding="utf-8",
        level=logging.INFO,
        format="%(message)s",
        force=True,
    )

    for arguments in (
        '{"previous_close": 10, "current_close": 9}',
        '{"previous_close": 0, "current_close": 9}',
    ):
        record = execute_tool("calculate_change", arguments)
        print(record.model_dump_json(indent=2))
    print(f"Log: {log_path}")


if __name__ == "__main__":
    main()
