# Day 10 Stock Profile Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现第二个工具 `get_stock_profile`，读取数据库中的股票代码和名称。

**Architecture:** Pydantic 校验股票代码，独立查询函数消费校验后的参数及调用方提供的 SQLAlchemy Session。函数返回本地已存资料；未知股票抛出明确异常。测试使用独立内存 SQLite，不连接行情服务或模型。

**Tech Stack:** Python 3.11+、Pydantic 2、SQLAlchemy 2、pytest、Ruff。

**Spec:** `docs/superpowers/specs/2026-10-08-day10-function-calling-design.md`

## Global Constraints

- 不新增依赖。
- 返回已保存的股票代码和名称。不得为缺失资料补造行业、财务或官方来源。
- 股票代码保持字符串。允许六位数字或六位数字加 `.SH`、`.SZ`、`.BJ` 后缀；去掉外围空白后精确匹配数据库记录。无后缀输入不会猜测交易所后缀。
- 参数拒绝额外字段，股票不存在抛出 `StockNotFoundError`。
- Day 10 全部验收前不得标记整天完成。

### Task 1: 股票资料参数与查询

**Files:** Create `app/tools/market_data.py`, `tests/unit/test_stock_profile_tool.py`; update `docs/day-10-function-calling.md`, `README.md`.

**Interfaces:** Consumes `StockProfileArguments`, SQLAlchemy `Session`; produces `get_stock_profile(arguments, session) -> dict[str, str]` and `StockNotFoundError`.

- [x] Write tests and an empty module. Seed two differently named stocks in an in-memory SQLite database. Query `000001.SZ` and assert exactly `{"stock_code": "000001.SZ", "name": "本地保存的名称甲"}`. Query an unknown code and assert `StockNotFoundError`. Validate that surrounding whitespace is stripped and invalid codes, missing fields, non-string inputs and extra fields raise `ValidationError`.
- [x] Run `./.venv/Scripts/python.exe -m pytest tests/unit/test_stock_profile_tool.py --confcutdir=tests/unit --tb=line`. Expected: failures for the absent argument model, no collection errors.
- [x] Implement the following code:

```python
from typing import Annotated
from pydantic import BaseModel, ConfigDict, StringConstraints
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.database import Stock

class StockNotFoundError(Exception):
    pass

class StockProfileArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")
    stock_code: Annotated[str, StringConstraints(
        strict=True, strip_whitespace=True,
        pattern=r"^[0-9]{6}(?:\.(?:SH|SZ|BJ))?$",
    )]

def get_stock_profile(
    arguments: StockProfileArguments, session: Session
) -> dict[str, str]:
    stock = session.scalar(select(Stock).where(Stock.symbol == arguments.stock_code))
    if stock is None:
        raise StockNotFoundError("股票不存在")
    return {"stock_code": stock.symbol, "name": stock.name}
```

- [x] Run targeted tests, then `./.venv/Scripts/python.exe -m pytest` and `./.venv/Scripts/ruff.exe check .`. Expected: all tests and lint pass; record existing warnings.
- [x] Update learning notes and README, commit this checkpoint with `git commit -m "Add Day 10 stock profile query tool"`. Explain query filtering and the unknown-stock branch in the same chat.

## 执行记录

沿用已批准的 Day 10 设计和当前 `codex/day10-function-calling` 分支。股票代码精确匹配的约定与现有 Day 7 查询一致；无后缀不会自动匹配带后缀记录。统一执行、日志与模型选择仍属于后续阶段。

- RED：17 条新测试失败于空模块缺少参数模型，测试正常收集。
- GREEN：17 条新增测试通过；全套 150 passed，2 条既有依赖警告；Ruff 通过。
- 已记录计算工具口头理解和需要巩固的字典/列表区别。股票查询代码的口头理解继续在当前聊天确认。
