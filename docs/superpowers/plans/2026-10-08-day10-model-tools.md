# Day 10 Model Tool Response Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans to implement this approved stage inline, with test-driven-development and verification-before-completion.

**Goal:** 让假模型和千问客户端支持原生工具调用响应，保留已有文本聊天行为。

**Architecture:** Pydantic 模型描述工具调用编号、函数名和原始 JSON 参数字符串；客户端增加 `chat_with_tools(messages, tools)`。共用 HTTP 请求、超时和错误处理，工具请求携带 `tools` 及 `tool_choice="auto"`。客户端只校验协议结构，业务参数由既有执行器校验。

**Spec:** `docs/superpowers/specs/2026-10-08-day10-function-calling-design.md`

**Scope:** 本次教学段实现客户端。下一段连接执行器；不实现 Day 11 自动循环，不把模拟 HTTP 测试称为真实模型验收。

### Task 1: 原生响应与客户端

Files: create `app/llm_types.py`, `tests/unit/test_tool_model_client.py`; update `app/llm_client.py`, README and Day 10 notes.

- [x] Write tests; run them before implementation to confirm missing functionality.
- [x] Define strict function name/arguments, call id/type and reply content/tool_calls. Null or missing tool_calls becomes an empty list; neither text nor calls is a protocol error.
- [x] Add the new method to Protocol, FakeModelClient and QwenModelClient. Preserve old chat request shape and behavior. Add optional configured tool reply to factory for offline tests.
- [x] Verify native request payload, tool/text responses, raw invalid argument preservation, malformed protocol rejection, timeout/auth/API/connection handling and offline factory behavior.
- [x] Run targeted tests, full pytest, Ruff and changed-file format checks; update learning notes and commit.
- [ ] Explain one short code section and ask one comprehension question before connecting the executor.

## Execution Notes

用户已批准逐段写和讲；最新能区分发给模型的 `tools` 与模型返回的 `tool_calls`。沿用当前学习目录和分支，不新增依赖。

- RED: 19 个新案例均因缺少客户端方法或响应模型失败。
- GREEN: 新旧客户端及工厂共 36 passed；全套 205 passed，2 条既有依赖警告。
- Ruff、相关文件格式与 diff 检查通过；未请求真实模型。
- 保持教学节奏：本段解释读取请求，下一段连接执行器。整天尚未完成。
