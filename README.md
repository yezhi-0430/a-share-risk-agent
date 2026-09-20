# A 股自选股风险监控与模拟交易 Agent

面向个人投资者的金融信息研究工作台。系统维护多只自选股，扫描公告、财报和日线指标中的风险线索，生成带来源的研究报告，并在用户确认后执行模拟交易。

## 当前进度

第 2 天：已完成股票查询和内存版自选股分组接口。当前数据在服务重启后会清空，第 3 天将接入数据库持久化。

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

## 当前接口

- `GET /api/v1/stocks?query=600519`：按代码或名称查询股票。
- `GET /api/v1/watchlists`：列出自选股分组。
- `POST /api/v1/watchlists`：创建分组。
- `PATCH /api/v1/watchlists/{id}`：重命名分组。
- `DELETE /api/v1/watchlists/{id}`：删除分组。
- `POST /api/v1/watchlists/{id}/items`：向分组添加股票。
- `DELETE /api/v1/watchlists/{id}/items/{symbol}`：从分组移除股票。

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
- [第 2 天 FastAPI 学习笔记](docs/day-02-fastapi-notes.md)
