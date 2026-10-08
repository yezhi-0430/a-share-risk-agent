# Day 10 Tool Execution Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 统一执行三个工具，并记录每次成功和失败尝试。

**Architecture:** 注册表提供工具白名单、参数模型和模型可读的描述及 Schema。执行入口先检查名称，再用模型校验原始 JSON；校验后才调用业务函数或创建数据库 Session。每次调用返回结构化记录并发送 INFO JSON 日志；离线演示配置 JSONL 文件输出。

**Tech Stack:** Python 3.11+、Pydantic 2、SQLAlchemy、logging、perf_counter、pytest。

**Spec:** `docs/superpowers/specs/2026-10-08-day10-function-calling-design.md`

## Global Constraints

- 不新增依赖。
- 无效参数不得进入业务函数。
- 每次尝试记录工具名称、原始参数、结果或错误和耗时。参数失败也记录。
- Day 10 使用结构化应用日志；数据库审计表由 Day 12 实现。
- 统一入口仅接受登记的工具名称。
- Day 10 全部验收前不得标记整天完成。

### Task 1: 注册、执行与日志

**Files:** Create `app/tools/registry.py`, `app/tools/executor.py`, `app/tools/demo.py`, `tests/unit/test_tool_executor.py`; update README and Day 10 learning notes.

**Interfaces:**
- Consumes: 三个已有工具及其参数模型；SQLAlchemy Session 和 SessionLocal。
- Produces: `tool_definitions() -> list[dict[str, object]]`；`execute_tool(tool_name: str, arguments: str, session: Session | None = None) -> ToolExecutionRecord`。
- `ToolExecutionRecord` 包含 `tool_name`、原始 JSON 字符串 `arguments`、`status`（success/error）、`result`、`error`（kind/message，内部失败附带可选 details）、非负 `duration_ms`。
- error.kind 允许 `unknown_tool`、`invalid_arguments`、`stock_not_found`、`execution_error`。

- [x] Write tests and empty modules. Spy on calculation, query and Session creation to prove rejection precedes execution; verify schema whitelist, successful calls, empty results, expected/unexpected errors, elapsed time and JSON logging.
- [x] Run `./.venv/Scripts/python.exe -m pytest tests/unit/test_tool_executor.py --confcutdir=tests/unit --tb=line`. Expected: missing-function failures.
- [x] Register exactly three parameter models and descriptions; generate each function definition using `model.model_json_schema()`. Implement the execution flow below, with the declared record model and error fields:

```text
start = perf_counter()
result = None; error = None
if tool_name is not registered:
    error = {kind: unknown_tool, message: 工具未注册}
else:
    try:
        validated = model.model_validate_json(arguments)
        if calculate_change:
            result = calculate_change(validated)
        elif a session is supplied:
            result = matching query(validated, session)
        else:
            with SessionLocal() as owned_session:
                result = matching query(validated, owned_session)
    except ValidationError:
        error = invalid_arguments + field locations and validation messages
    except StockNotFoundError:
        error = stock_not_found + 股票不存在
    except Exception as exc:
        error = execution_error + 工具执行失败 + exception type/message in details
record = declared fields, status derived from error, duration_ms from elapsed time
logger.info(record.model_dump_json())
return record
```

- [x] Add standalone `python -X utf8 -m app.tools.demo`: create `data/private`, configure UTF-8 JSONL logging with INFO level, execute a valid 10→9 call and a rejected 0→9 call, print both records and the log location. Calculation demo performs no model or database requests. Logs remain git-ignored.
- [x] Run targeted tests, full pytest, Ruff and format checks. Run the demo and inspect the generated file to confirm a successful and a rejected attempt.
- [x] Record results and commit with `git commit -m "Add audited Day 10 tool execution"`; teach whitelist and validation before execution in the current chat.

## 执行记录

三个业务工具已经实现。用户能判断日期闭区间筛选、日期倒序、空日线返回空列表和反向日期应拒绝。沿用已批准方案；本阶段不实现自动 Agent 循环或真实模型工具选择。

Ruling: 内部失败的异常类型和原因写入结构化 error.details，替代独立多行 traceback 日志，确保 JSONL 每行均为一个完整调用记录；这些诊断字段供应用审计使用。

- RED：15 个新案例均失败于空模块缺少相应功能。
- GREEN：15 个新增案例通过，全套 186 passed，2 条既有依赖警告；Ruff 通过。
- 离线演示已运行，成功与拒绝记录实际写入 JSONL，路径由 `.gitignore` 覆盖。
- Ruling: Windows 演示命令使用 `-X utf8`，因为实际 stdout 默认为 GBK，而工具界面读取 UTF-8；已验证中文输出正常。
- 模型工具选择仍待接入，口头理解继续在当前聊天确认。
