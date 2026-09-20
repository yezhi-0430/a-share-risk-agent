# A 股自选股风险监控与模拟交易 Agent

面向个人投资者的金融信息研究工作台。系统维护多只自选股，扫描公告、财报和日线指标中的风险线索，生成带来源的研究报告，并在用户确认后执行模拟交易。

## 当前进度

第 1 天：工程初始化。当前只提供服务健康检查，业务功能将在后续按测试驱动逐步加入。

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
