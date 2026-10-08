# Day 10 Real Tool Selection Verification Plan

> **For agentic workers:** Execute inline with test-driven-development and verification-before-completion; continue the approved staged teaching.

**Goal:** 使用既有本地千问配置验证一次真实工具选择与 Python 计算，并保留可重复运行的命令。

**Architecture:** 扩展现有演示命令，`--provider` 默认为 fake，显式 qwen 时经 Settings 与工厂使用真实客户端。默认 fake 覆盖 `.env` 中的 provider，避免学习演示无意发出真实请求。真实输入仅为虚构的昨日价格 10、今日价格 9；发送三个注册工具和 auto 选择，仍只有一轮模型请求。

**Constraints:** 不打印或修改密钥，不新增依赖；不写真实数据库数据；默认不请求真实服务。真实运行会使用本地服务配置发出 API 请求，已属于本次模型工具选择验收范围。日志继续仅收集执行器 JSON。

### Task 1: 可选择的演示与验收

Files: update `app/tool_calling_demo.py`, README, Day 10 notes and previous teaching plan; create `tests/unit/test_tool_calling_demo.py`.

- [x] Write two behavioral tests: default remains offline when environment selects qwen; explicit qwen goes through native client/registry/executor using MockTransport, exactly one request and correlated persisted result.
- [x] Observe failures, add argparse provider selection and model factory wiring; preserve existing fake demo.
- [x] Run targeted/full tests, Ruff and format checks.
- [x] Run exactly one real verification command (connection retry remains existing client policy), inspect selected name/arguments/result and appended JSONL. Record success or failure honestly; do not repeat unchanged requests merely to get a preferred answer.
- [x] Update evidence and learning notes; commit.
- [x] Explain the real result and complete the final comprehension check.

## Teaching Notes

用户最初不清楚空列表循环次数。解释后，能判断包含两个调用请求时循环两次；空列表和异常退出仍需后续新场景巩固。不把口头回答标记为可独立编写完整 Agent。

- RED: 2 个演示案例因缺少 HTTP 客户端接入而失败。
- GREEN: 演示、连接和工厂共 13 passed；全套 215 passed，2 条既有依赖警告；Ruff、格式与 diff 检查通过。
- 真实命令运行一次并成功：qwen-plus 选择 calculate_change，参数为昨日 10/今日 9，Python 返回 -10.0000；已核验追加 JSONL 的编号、参数、成功结果和耗时。
- 技术目标已验收。继续最后口头分工检查，下一天的自动循环不在本阶段实现。
- 最后问答已完成：用户回答“计算函数”，能判断真实样例的 -10.0000 由 Python 计算产生。本轮技术验收与基础问答完成；后续继续巩固循环及异常分支。
