# Day 10 One Tool Turn Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline, with test-driven-development and verification-before-completion.

**Goal:** 将模型返回的工具调用请求交给已有执行器，离线验证选择、校验、执行和记录的连接。

**Architecture:** `run_tool_turn(client, messages, session=None)` 发送注册表工具描述，调用一次 `chat_with_tools`，按顺序执行响应中的调用，返回 `ToolTurnResult(reply, executions)`。记录新增可选 `tool_call_id`，关联请求和结果。无工具请求时返回空执行列表。模型服务失败则抛出既有模型异常，不启动工具。

**Scope:** 一轮模型请求与受控工具执行。工具结果回传模型及自动循环属于 Day 11。假模型和 MockTransport 验证必须与真实模型验证分开记录。

**Spec:** `docs/superpowers/specs/2026-10-08-day10-function-calling-design.md`

### Task 1: 连接与离线演示

Files: create `app/tool_calling.py`, `app/tool_calling_demo.py`, `tests/unit/test_tool_calling.py`; update executor, README and learning notes.

- [x] Write tests and empty module; confirm missing-function failures.
- [x] Implement one-turn orchestration and optional call ID in returned/logged execution records.
- [x] Verify native HTTP request uses the three registered definitions; valid calculation/log correlation, invalid/broken parameters never enter calculation, unknown names never open Session, supplied-session profile query, text without execution, multiple calls and model failure without execution.
- [x] Add standalone fake demo with valid and zero-price calls. Configure a UTF-8 JSONL handler only for executor records; print result and log path. Do not make model/network/database requests in this demo.
- [x] Run targeted/full tests, Ruff and format checks; run demo and inspect persisted log.
- [x] Update documentation and commit.
- [ ] Explain the request-to-executor code and ask one question before real model verification.

## Execution Notes

用户能判断 `content=None` 但有结构合法的调用时应继续校验。沿用批准的逐段教学方案和当前分支；不新增依赖。

- RED: 8 个新增案例缺少入口/模块功能而失败。
- GREEN: 连接、执行器和工具协议相关测试共 42 passed；全套 213 passed，2 条既有依赖警告。
- Ruff、相关文件格式与 diff 检查通过。
- 已实际运行假模型演示并检查 JSONL 最后两条：合法计算成功，零价格拒绝，编号正确，私有文件仍被 Git 忽略。
- 未请求真实模型；一轮受控执行结束，不自动回传工具结果或继续模型推理。
