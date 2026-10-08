# Project Review Fixes

用户已要求修复整项目审查列出的七项问题；按审查中给出的目标实施，不新增课程功能。

## Design

- 日线 POST 使用专用 APIRoute/Request，以 Decimal 读取 JSON 小数，保留现有 JSON 数字和字符串接口及 OpenAPI 文档。
- 四个价格统一校验正数、有限值、最多 18 位/4 位小数；模型校验 low <= open/close <= high。
- 成交量存储为 BIGINT，输入限制在非负有符号 64 位范围内。
- 新增、查找和移除使用去空白、大写股票代码；迁移同步现有代码，遇到归一化冲突则回滚并报告，不猜测合并行情。
- Repository 在保存点内插入股票和关联，唯一冲突后重新查询股票或转换为重复关联错误，保留其他数据库错误。
- 风险接口的 fake 客户端返回合法摘要，明确离线未分析，risk_level=unknown，不编造事实或来源。
- 提供幂等 PostgreSQL schema upgrade 命令，保留已有数据，升级 volume 和股票代码；不在每次 HTTP 请求时迁移。

## Execution

- [x] Add regressions and observe failures before implementation: exact numeric HTTP prices, invalid scalar/OHLC prices, lowercase codes, concurrent creation/association, default fake response, BIGINT boundaries and existing-schema migration.
- [x] Implement the seven fixes and database upgrade command.
- [x] Run focused and full tests; lint/format; apply upgrade to configured local database and verify columns/data checks without exposing credentials.
- [x] Document results, migration command and limitations; commit verified changes.

既有工具接口及 Day 11 范围保持不变。只对本次修复补充验证，不重复请求真实模型。
