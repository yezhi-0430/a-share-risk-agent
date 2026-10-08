# Day 10 Calculation Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现并讲解 Day 10 的第一个工具 `calculate_change`。

**Architecture:** Pydantic 参数模型负责校验，业务函数消费校验后的参数并用 Decimal 计算。按用户批准的学习节奏，本计划仅覆盖计算工具；完整 Day 10 的执行入口、日志和模型选择继续按设计文档推进。

**Tech Stack:** Python 3.11+、Pydantic 2、标准库 decimal、pytest、Ruff。

**Spec:** `docs/superpowers/specs/2026-10-08-day10-function-calling-design.md`

## Global Constraints

- 不新增依赖。
- 价格精度与现有 `Numeric(18, 4)` 行情字段一致，即最多 18 位数字、4 位小数。
- 按 `(current_close - previous_close) / previous_close * 100` 计算，使用 `ROUND_HALF_UP` 保留四位小数。
- 接受 JSON 数字和合法十进制数字字符串，拒绝布尔值、缺失字段和额外字段。
- 第一阶段不代表 Day 10 全部完成。

### Task 1: 参数模型与计算函数

**Files:**
- Create: `app/tools/__init__.py`
- Create: `app/tools/calculations.py`
- Test: `tests/unit/test_calculation_tool.py`
- Create: `docs/day-10-function-calling.md`
- Modify: `README.md` 当前进度与学习记录链接。

**Interfaces:**
- Consumes: 原始参数字典供 `CalculateChangeArguments.model_validate` 校验。
- Produces: `CalculateChangeArguments` 和 `calculate_change(arguments: CalculateChangeArguments) -> dict[str, str]`。

- [x] **Step 1: Write failing tests and empty module skeletons**

测试核心内容如下，并在同一测试文件参数化覆盖涨跌持平、十进制价格、正负舍入以及设计列出的所有无效输入。

```python
from app.tools import calculations

def test_calculates_fall():
    arguments = calculations.CalculateChangeArguments.model_validate(
        {"previous_close": 10, "current_close": 9}
    )
    assert calculations.calculate_change(arguments) == {"change_percent": "-10.0000"}
```

- [x] **Step 2: Observe missing-feature failures**

Run: `./.venv/Scripts/python.exe -m pytest tests/unit/test_calculation_tool.py --confcutdir=tests/unit`

Expected: 测试失败于空模块没有 `CalculateChangeArguments` 属性，测试可以正常收集。

- [x] **Step 3: Implement the smallest validated calculation**

```python
from decimal import ROUND_HALF_UP, Decimal
from pydantic import BaseModel, ConfigDict, Field

class CalculateChangeArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    previous_close: Decimal = Field(
        gt=0, allow_inf_nan=False, max_digits=18, decimal_places=4
    )
    current_close: Decimal = Field(
        gt=0, allow_inf_nan=False, max_digits=18, decimal_places=4
    )

def calculate_change(arguments: CalculateChangeArguments) -> dict[str, str]:
    change_percent = (
        (arguments.current_close - arguments.previous_close)
        / arguments.previous_close
        * Decimal("100")
    )
    rounded = change_percent.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    return {"change_percent": str(rounded)}
```

- [x] **Step 4: Verify targeted tests, regressions and lint**

Run: `./.venv/Scripts/python.exe -m pytest tests/unit/test_calculation_tool.py --confcutdir=tests/unit`

Expected: 全部新增案例通过。

Run: `./.venv/Scripts/python.exe -m pytest`

Expected: 新增和既有测试全部通过；明确记录既有依赖警告。

Run: `./.venv/Scripts/ruff.exe check .`

Expected: All checks passed.

- [x] **Step 5: Record learning status and explain the first code section**

学习记录明确分开实现状态、测试结果、待完成事项和已口头确认的概念。README 标记 Day 10 进行中。最终向用户展示参数模型片段，说明 `Decimal`、`Field(gt=0)`、`extra="forbid"`，以一次一题的方式确认理解。

- [x] **Step 6: Commit verified calculation checkpoint**

Run: `git add app/tools tests/unit/test_calculation_tool.py docs/day-10-function-calling.md docs/superpowers/plans/2026-10-08-day10-calculation-tool.md README.md`

Run: `git commit -m "Add validated Day 10 calculation tool"`

Expected: 仅提交本学习阶段的文件；后续 Day 10 任务尚未完成。

## 执行记录

- 用户已批准设计并要求逐段写和讲；本计划在当前聊天内执行，仅覆盖第一阶段。
- 工作目录沿用当前学习项目，使用 `codex/day10-function-calling` 分支。设计已在 `9bc0c5d` 提交。
- 测试基线：49 个离线单元测试通过。
- RED：31 个新案例均失败于空模块缺少 `CalculateChangeArguments`，证明目标功能尚不存在。
- GREEN：31 个新案例通过；全套 133 passed，2 条既有依赖警告；Ruff 通过。
- 口头代码理解仍在进行，不能把实现完成记为用户已经掌握。
