# Day 8：大模型 API 基础

## 今天的目标与范围

- 理解 system、user、assistant、tool 消息，以及 Token、上下文和流式输出。
- 使用统一的 `chat(messages) -> str` 接口切换假模型和千问。
- 为千问请求设置超时、有限重试和明确的错误类型。
- 自动测试始终使用假 HTTP 响应，不依赖网络或真实 API Key。

本日只实现非流式文本回答。工具调用、结构化输出和流式接收留在后续课程。

## 关键概念

模型只看到本次发送的 `messages`。上一轮回答如果再次发送，就属于本次输入 Token。流式输出会逐段返回内容；需要完整 JSON 时，应收齐后再解析。

`system` 放长期的任务与回答要求，`user` 放当前问题，`assistant` 放需要带入的历史回答，`tool` 放程序执行工具后的结果。API Key 只用于 HTTP 鉴权请求头，不进入 `messages`。

## 代码结构

- `app/config.py`：从环境变量读取 `MODEL_PROVIDER`、`MODEL_NAME`、`MODEL_BASE_URL` 和 `DASHSCOPE_API_KEY`。默认选择假模型。
- `app/llm_client.py`：`FakeModelClient` 和 `QwenModelClient` 都提供 `chat(messages)`；`create_model_client()` 按配置选择。调用者创建并关闭传入的 `httpx.Client`。
- `tests/unit/`：用固定回复和 `httpx.MockTransport` 验证请求与错误处理。

千问北京地域的默认地址是通用按量调用地址。项目后端需使用按量付费 API Key；Token Plan 与 Coding Plan 的专属 Key 仅供指定 AI 工具交互使用，不适合本项目后端。若使用按量付费业务空间专属域名，`MODEL_BASE_URL` 必须与 Key 对应；请以控制台和[官方 Base URL 说明](https://help.aliyun.com/zh/model-studio/base-url)为准。

## 超时、重试和错误

- 每次请求设置 10 秒的 HTTPX 超时。它限制连接、读写等网络等待阶段，并非整段回答的总时长上限。
- 仅对连接失败再试一次，总尝试次数最多两次。读取超时不自动重试，因为请求可能已被服务端处理，再发可能造成重复调用。
- 读取超时映射为 `ModelTimeoutError`；连接重试耗尽映射为 `ModelConnectionError`。
- HTTP 401 映射为 `ModelAuthenticationError`；其他 HTTP 4xx/5xx 映射为带状态码的 `ModelAPIError`，均不自动重试。
- 无法解析的 JSON、缺失的回答字段或非文本回答映射为 `ModelResponseError`。
- 千问模式缺少 Key 时，`create_model_client()` 抛出 `ModelConfigurationError`。错误消息不包含 Key。

## 验证方式

离线运行：

```powershell
python -m pytest tests/unit --confcutdir=tests/unit
ruff check .
```

首次真实调用需要先在本地 `.env` 中设置 `MODEL_PROVIDER=qwen`、`MODEL_NAME=qwen-plus` 和与 `MODEL_BASE_URL` 配套的按量付费 `DASHSCOPE_API_KEY`。不要把真实 Key 写入测试、提交到 Git 或贴进聊天。然后可在项目根目录自行运行：

```powershell
@'
import httpx

from app.config import Settings
from app.llm_client import create_model_client

with httpx.Client() as http_client:
    model = create_model_client(Settings(), http_client)
    answer = model.chat([{"role": "user", "content": "Explain a stock daily price record in one short English sentence."}])
    print(answer)
'@ | .\.venv\Scripts\python.exe -
```

上述真实调用会产生服务商请求及可能的费用。用户已在本地按此方式完成一次真实千问调用，模型返回了对股票日线数据的解释。离线测试只证明程序按约定组装请求、读取响应和处理失败；真实服务可用性仍需以当时所用账号和配置为准。
这里故意使用英文测试问题，避免部分 Windows PowerShell 终端在向 Python 管道传递中文源码时出现乱码。后续正式使用中文问题时，可将 Python 代码保存为 UTF-8 文件再运行。

## 学习复盘

- 实现状态：已完成模型客户端、配置切换与错误处理；已在本地完成一次真实服务调用。
- 技术复盘：已梳理消息上下文、密钥位置、假模型用途、超时与重试边界；全套测试和代码检查通过。
- 学习复盘：2026-10-07 已完成基础概念问答；尚未通过独立编写代码验证熟练程度。

## 本次学习复盘记录

- 已通过问答确认：消息角色的基本用途、历史消息再次发送会计入本次输入 Token、API Key 用于鉴权、修改 `MODEL_NAME` 可切换账号可用的千问型号，以及流式输出和工具结果消息的概念。
- 已补齐连续对话的组织方式：发送需要的历史用户问题、模型回答和当前问题；历史模型回答使用 `assistant` 角色。
- 已补齐统一客户端接口的作用：客户端都提供 `chat(messages) -> str`，由工厂按配置选择，业务调用方式保持一致。
- 已纠正超时与重试的区别：超时用于停止过长的等待并报告失败；当前代码遇到超时不自动重试，连接失败最多尝试两次。
- 已纠正自动测试的验证范围：使用假 Key 和模拟 HTTP 响应，不调用真实账号；自动测试通过无法证明真实 Key 或服务可用，真实调用需要单独验证。
- 后续巩固：独立组装一段连续对话的 `messages`，并阅读 `create_model_client()` 和 `chat()` 的选择及错误处理流程。流式接收与实际工具调用尚未实现。
