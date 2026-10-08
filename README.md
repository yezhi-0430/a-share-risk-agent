# A 股自选股风险监控与模拟交易 Agent

面向个人投资者的金融信息研究工作台。系统维护多只自选股，扫描公告、财报和日线指标中的风险线索，生成带来源的研究报告，并在用户确认后执行模拟交易。

## 当前进度

Day 1–7 已完成后端、自选股管理和日线导入查询。Day 8 已加入可切换的假模型与千问客户端，离线测试通过，并已在本地完成一次真实千问调用。第一版界面尚未完成。

Day 9 已加入风险摘要结构校验与接口，20 条模拟输出验收通过，并完成一次真实千问结构化输出验证。格式校验不验证事实真伪。

Day 10 进行中：已实现 `calculate_change`、`get_stock_profile`、`get_daily_prices` 三个独立工具及参数校验。新增 69 个工具测试通过，全套测试 171 passed。统一执行入口、调用日志和模型选择工具尚待逐步完成。

## 项目原则

- 一级事实以交易所、巨潮资讯和上市公司正式披露为准。
- 所有重要结论保留来源、发布时间和采集时间。
- 模型负责理解、检索编排和解释；金额与指标由确定性代码计算。
- Agent 不能直接交易，模拟操作必须经过用户确认。
- 项目不构成投资建议，不接入真实券商账户。

## 本地运行

要求 Python 3.11 或更高版本。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
uvicorn app.main:app --reload
```

打开：

- API 文档：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>

运行检查：

```powershell
pytest
ruff check .
```

模型客户端的配置、离线测试和手动验证方式见 [Day 8 学习记录](docs/day-08-model-api.md)。
风险摘要的数据结构、接口与验证结果见 [Day 9 学习记录](docs/day-09-structured-output.md)。
工具调用的学习进度与计算工具说明见 [Day 10 学习记录](docs/day-10-function-calling.md)。

## 目录

```text
app/                 应用代码
tests/               自动化测试
docs/                架构和设计记录
data/                 可公开的演示数据
```

详细设计见：

- [产品范围与用户故事](docs/product-scope.md)
- [第一版架构](docs/architecture.md)
