# Day 10：Function Calling（进行中）

## 今天的目标

实现 `get_stock_profile`、`get_daily_prices`、`calculate_change` 三个工具。参数校验成功后才执行业务函数；记录每次调用的名称、参数、结果或错误和耗时；让模型按工具清单选择工具。

## 已口头确认的概念（2026-10-08）

- 最初认为模型给出 JSON 就算已经执行；说明“调用请求”和“程序实际运行”的区别后，能够判断程序不调用函数时，工具不会自己运行。
- 能判断昨日收盘价为零时应拒绝计算，并解释收盘价必须大于零。
- 能为日线查询问题选出 `get_daily_prices`。
- 能区分 `arguments` 中的查询条件与工具执行后的结果。
- 能说明被拒绝的调用也要记录，以便后续查看失败原因。
- 能判断负价格被 `gt=0` 拒绝；能计算 20 元涨至 21 元的涨跌幅为 5%。
- 最初把 `{"change_percent": "5.0000"}` 误认为列表；说明 `{}` 字典与 `[]` 列表的区别后，能在新的股票资料例子中判断字典。类型区分仍需通过后续情景巩固。
- 能判断即使两个价格合法，多出 `risk_level` 也不能通过 `extra="forbid"` 校验。
- 能判断只有另一只股票的记录时，查询目标代码会得到 `None`。
- 最初认为 `raise` 后还会执行 `return`；说明抛出异常会退出当前函数后，能判断“已找到股票”会返回代码和名称。异常分支仍需用新的场景确认。
- 能判断日期闭区间 24–25 日包含 24 和 25 日，日期降序让 25 日排在第一条；能判断股票存在但范围内没有日线应返回空列表。
- 能判断开始日期 26 日、结束日期 24 日应拒绝调用，而不是查询后返回空列表。
- 能判断合法 JSON 不能绕过工具白名单，未注册的 `delete_stock` 不能执行。
- 能区分请求中发给模型的工具描述 `tools` 与模型响应中的调用请求 `tool_calls`。

上述记录反映当前口头理解，不代表已能独立编写工具执行器或完整 Agent 循环。

## 第一阶段：计算工具

代码：`app/tools/calculations.py`。

`CalculateChangeArguments` 用 Pydantic 定义 `previous_close` 和 `current_close`。二者均为必填 `Decimal`：

- `gt=0`：必须大于零。
- `allow_inf_nan=False`：拒绝无穷大和 NaN。
- `max_digits=18, decimal_places=4`：精度与行情表 `Numeric(18, 4)` 一致，超出约定精度则拒绝输入。
- `extra="forbid"`：拒绝额外参数；这比 Day 9 风险摘要默认忽略额外字段更严格。

接受 JSON 数字和合法十进制数字字符串。数字字符串可衔接现有日线查询返回的价格字符串。布尔值、普通文字、缺失字段等不能通过校验。

`calculate_change(arguments)` 的输入是已经校验过的参数模型。公式为：

```text
涨跌幅百分数 = (今日收盘价 - 昨日收盘价) / 昨日收盘价 × 100
```

用 Decimal 计算，以 `ROUND_HALF_UP` 保留四位小数。输入 10 和 9，输出：

```json
{"change_percent": "-10.0000"}
```

`change_percent` 的单位是百分数，因此此结果表示 -10%；字符串保留十进制表示。输入价格精度限制与计算结果舍入是两件事。

本阶段可直接用 `CalculateChangeArguments.model_validate(...)` 校验后调用函数。统一执行入口尚未实现，不能把参数模型测试当作“模型错误参数不会进入业务函数”的完整集成验收。

## 验证证据

测试文件：`tests/unit/test_calculation_tool.py`。

- 8 条计算样例：上涨、下跌、持平、小数价格、正负舍入和价格精度边界。
- 1 条验证整数、小数和数字字符串转为 Decimal 的样例。
- 22 条无效输入样例：零、负数、非数值、布尔值、null、列表、非有限价格、超出精度、缺失字段和额外字段。

先建立空模块并运行测试，观察 31 条均因缺少参数模型而失败；实现后 31 条均通过。2026-10-08 运行全套 `pytest`：133 passed，另有两条既有依赖弃用警告。全项目 `ruff check .` 通过，新增 Python 文件格式检查通过。测试不请求模型服务。

## 后续学习步骤

1. 继续通过实际代码确认参数模型、返回类型和 Decimal 的理解。
2. 继续讲解日线查询的日期范围、排序和空结果；三个独立工具均已实现。
3. 讲解已实现的工具白名单、统一参数校验与调用记录，巩固校验先于业务执行。
4. 扩展假模型和千问客户端的工具选择响应，完成离线验收并单独记录真实验证状态。

Day 10 尚未完成。工具结果回传模型并自动继续推理的循环属于 Day 11。

## 第二阶段：股票资料工具

代码：`app/tools/market_data.py`。

`StockProfileArguments` 只允许 `stock_code`。股票代码必须为字符串，允许六位数字或六位数字加大写 `.SH`、`.SZ`、`.BJ` 后缀；外围空白会去掉。六位数字输入只精确匹配数据库中同样的六位代码，不推测交易所后缀。现有项目的示例记录使用 `000001.SZ` 等完整代码。

`get_stock_profile(arguments, session)` 使用调用方提供的 Session 查询 `stocks` 表，条件为 `Stock.symbol == arguments.stock_code`。找到时返回：

```json
{"stock_code": "000001.SZ", "name": "本地保存的名称甲"}
```

名称来自本地记录；股票代码不会被用来推测名称。当前表没有行业等更多资料，因此不生成这些字段。数据库未匹配到记录时，抛出 `StockNotFoundError("股票不存在")`，供后续统一执行入口转换为失败结果并记录日志。

测试：`tests/unit/test_stock_profile_tool.py` 使用独立的内存 SQLite，包含 2 条已知股票查询、2 条未知或代码形式不匹配的查询、1 条外围空白归一化、12 条无效参数。共 17 条先失败、再通过；参数测试尚不代表统一执行入口的完整验收。

2026-10-08 本阶段全套测试结果为 150 passed，另有两条既有依赖弃用警告。全项目 Ruff 与新增文件格式检查通过。执行入口、调用日志、日线工具和模型工具选择仍待完成，未发起真实模型调用。

## 第三阶段：日线查询工具

代码仍在 `app/tools/market_data.py`。

`DailyPricesArguments` 继承股票代码校验及额外字段拒绝规则，增加必填 `start_date` 和 `end_date`。外部日期使用 `YYYY-MM-DD`，先转换为 Python `date`，拒绝无效日历日期、数值时间戳和日期时间输入，再检查开始日期不晚于结束日期；同一天作为开始和结束合法。

`get_daily_prices(arguments, session)` 先查股票，再按 `stock_id` 和日期筛选日线：

```python
DailyPrice.trade_date >= arguments.start_date
DailyPrice.trade_date <= arguments.end_date
```

筛选范围包含两端日期，结果按 `trade_date.desc()` 排序，即最新日期在前。每条记录包含日期、开高低收价格及成交量；价格沿用 Decimal 转字符串，日期转 ISO 字符串。

- 股票在本地不存在：抛出 `StockNotFoundError`。
- 股票存在但没有日线，或范围内没有日线：返回空列表 `[]`，不补造数据。

新增 `tests/unit/test_daily_prices_tool.py` 的 21 条样例，覆盖股票与日期过滤、排序和精度、单日范围、两种空结果、未知股票、日期转换、12 条非法参数和3条缺失参数。查询测试沿用虚构数据。两个数据库工具共用 `tests/unit/conftest.py` 的独立内存 SQLite fixture，测试不请求模型或行情服务。

TDD 记录：21 个新案例先因缺少模型或函数失败，既有股票工具的 17 条测试保持通过；实现后这 38 条全部通过。2026-10-08 最新全套结果为 171 passed，2 条既有依赖警告；全项目 Ruff 和相关文件格式检查通过。

三个独立业务工具已实现。统一执行入口、参数失败不进入业务函数的集成验证、调用日志和模型工具选择尚未完成，因此 Day 10 仍在进行中。

## 第四阶段：统一执行与调用日志

- `app/tools/registry.py`：只注册三个既有工具，提供参数模型、描述和 `tool_definitions()`，用于后续发送给模型的工具清单。
- `app/tools/executor.py`：`execute_tool(tool_name, arguments, session=None)` 接收工具名称和原始 JSON 参数字符串。先检查白名单，再用对应模型的 `model_validate_json` 校验，成功后才进入计算函数或查询函数。未提供 Session 时，仅在查询参数合法后打开应用数据库 Session；计算工具不打开数据库。
- `app/tools/demo.py`：离线执行一次正常计算和一次无效参数调用，把 JSON 记录追加到私有日志文件。

每条 `ToolExecutionRecord` 包含工具名、原始参数字符串、success/error 状态、结果或错误以及毫秒耗时。错误分类为 unknown_tool、invalid_arguments、stock_not_found、execution_error；校验错误保留字段位置和原因，内部执行错误的诊断保存在可选 `error.details` 中。即使原始 JSON 破损，也保留原文并返回失败记录。

每次调用返回完整记录，并通过 `app.tools.executor` 的 INFO 日志输出一行 JSON。应用调用方需配置日志处理器和 INFO 级别，才能把日志保存到文件；返回记录本身不依赖日志配置。演示已配置 UTF-8 JSONL 文件日志，运行方式为：

```powershell
.\.venv\Scripts\python.exe -X utf8 -m app.tools.demo
```

文件：`data/private/day10-tool-calls.jsonl`（已被 Git 忽略，重复演示会追加记录）。已运行并核验文件：正常计算记录的 result 为 `{"change_percent": "-10.0000"}`；被拒绝记录的 result 为 null，error.kind 为 invalid_arguments，错误说明昨日价格必须大于零，两者都有耗时。

终端编码检查发现普通 Python 管道 stdout 使用 GBK，造成工具界面按 UTF-8 读取时中文乱码；文件日志的 UTF-8 编码正常。使用 `-X utf8` 运行演示后，终端中文恢复正常。此处修正运行命令，没有修改业务计算逻辑。

新增执行与日志测试 15 条，先因缺少入口或注册表功能失败，再全部通过。通过业务函数调用计数证明零价格、缺失/额外字段、破损 JSON 和非对象根节点不会进入计算函数；反向日期不会进入查询或打开 Session；未知工具不会打开数据库。另验证成功查询、空结果、未知股票、内部失败、计时和成功/失败日志。

最新全套测试为 186 passed，2 条既有依赖警告；Ruff 和新增文件格式检查通过。当前仅实现确定性工具执行，模型还没有实际选择工具。Day 10 仍在进行中，自动循环留在 Day 11。

## 第五阶段之一：模型客户端读取工具请求

- `app/llm_types.py`：`FunctionCall` 描述函数名称及原始 JSON 参数字符串；`ToolCall` 额外保存调用 `id` 和 `type="function"`；`ToolReply` 包含文本 `content` 和调用列表 `tool_calls`。
- `app/llm_client.py`：保留原有 `chat(messages) -> str`，增加 `chat_with_tools(messages, tools) -> ToolReply`。千问客户端发送 `tools` 和 `tool_choice="auto"`，由模型决定是否调用工具；假模型可以配置固定工具响应。

模型发起工具调用时，`content` 可以为 null。若直接回复文本，缺失或 null 的 `tool_calls` 会归一化为 `[]`；两者都没有则拒绝。客户端校验工具协议结构，要求调用编号、函数名称和字符串形式的参数，不在这一层解析业务参数。因此即使参数字符串为破损 JSON，也先保留原文；下一段交给执行器拒绝并记录。

HTTP 请求、10 秒超时、一次连接失败重试及鉴权/API 错误处理由两种聊天方法共用。原来的文本请求不增加 `tools` 字段，Day 9 的文本与风险摘要行为保持通过。

测试：`tests/unit/test_tool_model_client.py`，19 个新案例先因缺少方法/响应模型失败，实现后通过。验证请求结构、文本与工具响应、原始无效参数保留、协议格式拒绝、响应外壳错误、超时与鉴权/API 错误、连接重试以及假模型工厂不发 HTTP。新旧客户端及工厂共 36 个案例通过。

2026-10-08 最新全套为 205 passed，2 条既有依赖警告；全项目 Ruff、修改文件格式与 diff 空白检查通过。本阶段只用假模型和 MockTransport，没有请求真实模型。模型响应与工具执行器尚未连接，Day 10 继续进行；连接和真实调用状态将单独记录。

协议参考：[阿里云 Function Calling 文档](https://help.aliyun.com/zh/model-studio/qwen-function-calling)。
