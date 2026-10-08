# Day 10：工具调用设计

用户于 2026-10-08 确认本方案，并选择先从 `calculate_change` 开始，逐段实现和讲解。

## 目标与学习顺序

完成三个工具、执行前参数校验、调用记录和模型选择工具。学习按小步推进：先计算工具，再数据库查询工具，最后统一执行与模型调用。每一步提供测试证据和口头理解检查，Day 10 全部验收前不得标记整天完成。

## 工具与输入输出

- `calculate_change`：输入 `previous_close`、`current_close`。参数使用 Pydantic 校验为有限且大于零的 `Decimal`；接受 JSON 数字和合法十进制数字字符串，拒绝布尔值、缺失字段和额外字段。价格精度与现有 `Numeric(18, 4)` 行情字段一致，即最多 18 位数字、4 位小数。按 `(current_close - previous_close) / previous_close * 100` 计算，使用 `ROUND_HALF_UP` 保留四位小数，输出 `{"change_percent": "-10.0000"}`。字段单位是百分数，字符串保持小数精度。
- `get_stock_profile`：输入字符串 `stock_code`，读取本地 `stocks`，返回已保存的股票代码和名称。不得为缺失资料补造行业、财务或官方来源。
- `get_daily_prices`：输入 `stock_code`、`start_date`、`end_date`，校验日期有效且开始日期不晚于结束日期；闭区间过滤本地日线，沿用最新交易日在前、价格为字符串的约定。区分股票不存在与股票存在但没有日线。

## 模块与流程

`app/tools/` 保存工具参数模型和业务函数，避免把模型协议放入已有 HTTP 路由。统一入口仅接受登记的工具名称，先解析和校验参数，再调用业务函数。无效参数不得进入业务函数。

每次尝试记录工具名称、原始参数、结果或错误和耗时。参数失败也记录。Day 10 使用结构化应用日志；数据库审计表由 Day 12 实现。

模型客户端增加工具调用能力，使用供应商的 `tools` 和 `tool_calls` 协议，同时保留已有 `chat(messages) -> str` 行为。假模型及模拟 HTTP 响应承担离线测试；是否完成真实调用须单独记录。参考：https://help.aliyun.com/zh/model-studio/qwen-function-calling 。

Day 11 实现把工具结果回传模型并继续推理的自动循环、最大步数与终止条件。Day 10 的验收聚焦工具选择及受控执行。

## 第一阶段接口与验收

创建 `app/tools/calculations.py`：

- `CalculateChangeArguments`：上述计算参数的 Pydantic 模型。
- `calculate_change(arguments: CalculateChangeArguments) -> dict[str, str]`：消费经过校验的参数，返回 `change_percent`。

第一阶段验证涨、跌、持平、小数价格和舍入；验证零、负数、错误类型、非有限价格、缺失字段、额外字段和超出精度的输入被拒绝。统一入口拒绝执行及日志测试归属于后续阶段，此时不能宣称它们已完成。

## 方案比较与决策

选择独立工具模块和统一执行入口，以便分别学习和测试参数、计算、数据库和模型协议。把工具逻辑直接放入 HTTP 路由虽减少文件，但会混合职责，不采用。沿用现有项目依赖和数据结构，第一阶段不新增依赖。
