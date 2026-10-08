# Day 10 Decimal JSON Parsing Fix

**Goal:** 修复审查发现的 P2：工具参数中的 JSON 小数在校验前经过 float，导致价格精度损失及非法精度通过校验。

**Approved scope:** 恢复既有价格精度约定，保持工具名称、参数格式、返回结果和日志接口。用户在审查后询问修复状态，本次完成该项修复。

**Approach:** 使用标准库 JSON 解析并以 Decimal 读取小数，再用既有 Pydantic 模型校验。破损 JSON 仍返回 invalid_arguments，原始参数字符串保持在日志中。计算函数本身不改变。

- [x] Add regression cases for valid 18-digit JSON numbers and over-precise numeric literals, including the connected tool turn; confirm failures before changing implementation.
- [x] Preserve decimal precision in argument decoding and keep JSON decoding failures as invalid_arguments.
- [x] Run affected tests, full suite, Ruff/format checks and offline demo; inspect the resulting logs.
- [x] Record corrected evidence and commit.

## Verification

- RED: 6 new regressions failed; 23 existing related cases passed.
- GREEN: 60 calculation/executor/tool-turn cases passed; full suite 221 passed, 2 existing dependency deprecation warnings.
- Ruff, changed-file formatting and diff whitespace checks passed.
- Offline demo exited normally, and the last two persisted JSONL entries were verified for valid result and invalid_arguments rejection.
- Pending teaching task: resume Day 10 oral review at question 1. No additional real model request was made.
