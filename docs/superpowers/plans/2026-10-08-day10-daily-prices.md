# Day 10 Daily Prices Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成第三个工具 `get_daily_prices`，按股票和日期闭区间读取日线。

**Architecture:** `DailyPricesArguments` 继承已验证的股票代码模型，增加日期类型及顺序校验。查询函数接收调用方提供的 Session，先确认股票存在，再过滤对应日线。测试共用内存 SQLite fixture。

**Tech Stack:** Python 3.11+、Pydantic 2、SQLAlchemy 2、pytest、Ruff。

**Spec:** `docs/superpowers/specs/2026-10-08-day10-function-calling-design.md`

## Global Constraints

- 不新增依赖。
- 校验日期有效且开始日期不晚于结束日期；闭区间过滤本地日线，沿用最新交易日在前、价格为字符串的约定。
- 区分股票不存在与股票存在但没有日线。
- 股票代码沿用 `StockProfileArguments` 的精确匹配与额外字段拒绝规则。
- 对外日期参数使用 `YYYY-MM-DD`，拒绝时间戳、日期时间字符串及其他非法类型；内部允许纯 `date` 对象。
- Day 10 全部验收前不得标记整天完成。

### Task 1: 日线参数与数据库读取

**Files:** Modify `app/tools/market_data.py`, `tests/unit/test_stock_profile_tool.py`; create `tests/unit/conftest.py`, `tests/unit/test_daily_prices_tool.py`; update README and Day 10 learning notes.

**Interfaces:** Consumes existing `StockProfileArguments`, SQLAlchemy `Session`, `Stock`, `DailyPrice`; produces `DailyPricesArguments` and `get_daily_prices(arguments, session) -> list[dict[str, object]]`.

- [x] Write tests for stock/date filtering, descending order, endpoint inclusion, single-day ranges, empty results and missing stocks. Also reject invalid calendars, reversed ranges, missing fields, extra fields, timestamp/date-time inputs and invalid stock-code types. Move the existing SQLite fixture to unit conftest without changing its behavior.
- [x] Run `./.venv/Scripts/python.exe -m pytest tests/unit/test_daily_prices_tool.py tests/unit/test_stock_profile_tool.py --confcutdir=tests/unit --tb=line`. Expected: old profile tests pass and new tests fail because `DailyPricesArguments` or `get_daily_prices` is missing.
- [x] Add `date`, `fullmatch`, `Self`, `field_validator`, `model_validator`, `DailyPrice` imports and implement:

```python
class DailyPricesArguments(StockProfileArguments):
    start_date: date
    end_date: date

    @field_validator("start_date", "end_date", mode="before")
    @classmethod
    def parse_date(cls, value: object) -> date:
        if type(value) is date:
            return value
        if isinstance(value, str) and fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            return date.fromisoformat(value)
        raise ValueError("日期必须使用 YYYY-MM-DD 格式")

    @model_validator(mode="after")
    def validate_date_range(self) -> Self:
        if self.start_date > self.end_date:
            raise ValueError("开始日期不能晚于结束日期")
        return self

def get_daily_prices(arguments: DailyPricesArguments, session: Session) -> list[dict[str, object]]:
    stock = session.scalar(select(Stock).where(Stock.symbol == arguments.stock_code))
    if stock is None:
        raise StockNotFoundError("股票不存在")
    prices = session.scalars(
        select(DailyPrice).where(
            DailyPrice.stock_id == stock.id,
            DailyPrice.trade_date >= arguments.start_date,
            DailyPrice.trade_date <= arguments.end_date,
        ).order_by(DailyPrice.trade_date.desc())
    ).all()
    return [
        {"trade_date": item.trade_date.isoformat(), "open": str(item.open),
         "high": str(item.high), "low": str(item.low), "close": str(item.close),
         "volume": item.volume}
        for item in prices
    ]
```

- [x] Run the targeted tests, full pytest, Ruff lint and format checks. Expected: all pass, with existing dependency warnings reported separately.
- [x] Record the teaching checkpoint, commit with `git commit -m "Add Day 10 daily price query tool"`, and explain date filtering and empty-result semantics in the current chat.

## 执行记录

沿用用户批准的 Day 10 方案，先完成三个独立工具，再进入统一执行、日志和模型选择。用户在说明异常分支后，能判断已查到股票时会返回代码和名称；`raise` 中断执行仍需巩固。

- RED：21 个新增案例因缺少日线模型或函数失败；17 个既有股票资料案例通过。
- GREEN：两个查询工具的 38 条测试全部通过；全套 171 passed，2 条既有依赖警告；Ruff 与格式检查通过。
- 日期过滤、排序和空结果的口头理解继续在当前聊天确认；尚不标记用户已掌握。
