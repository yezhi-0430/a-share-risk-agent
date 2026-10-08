from typing import Protocol

import httpx
from pydantic import ValidationError

from app.config import Settings
from app.llm_types import ToolReply


class ModelTimeoutError(Exception):
    pass


class ModelConnectionError(Exception):
    pass


class ModelAuthenticationError(Exception):
    pass


class ModelAPIError(Exception):
    def __init__(self, status_code: int) -> None:
        self.status_code = status_code
        super().__init__(f"模型接口返回 HTTP {status_code}")


class ModelResponseError(Exception):
    pass


class ModelConfigurationError(Exception):
    pass


class ModelClient(Protocol):
    def chat(self, messages: list[dict[str, str]]) -> str: ...

    def chat_with_tools(
        self, messages: list[dict[str, str]], tools: list[dict[str, object]]
    ) -> ToolReply: ...


class FakeModelClient:
    def __init__(self, reply: str, tool_reply: ToolReply | None = None) -> None:
        self.reply = reply
        self.tool_reply = tool_reply

    def chat(self, messages: list[dict[str, str]]) -> str:
        return self.reply

    def chat_with_tools(
        self, messages: list[dict[str, str]], tools: list[dict[str, object]]
    ) -> ToolReply:
        if self.tool_reply is not None:
            return self.tool_reply
        return ToolReply(content=self.reply)


class QwenModelClient:
    def __init__(
        self,
        api_key: str,
        http_client: httpx.Client,
        model_name: str = "qwen-plus",
        base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    ) -> None:
        self.api_key = api_key
        self.http_client = http_client
        self.model_name = model_name
        self.chat_url = f"{base_url.rstrip('/')}/chat/completions"

    def chat(self, messages: list[dict[str, str]]) -> str:
        message = self._request_message(messages)
        try:
            content = message["content"]
        except KeyError as exc:
            raise ModelResponseError("模型响应格式无效") from exc
        if not isinstance(content, str):
            raise ModelResponseError("模型回答不是文本")
        return content

    def chat_with_tools(
        self, messages: list[dict[str, str]], tools: list[dict[str, object]]
    ) -> ToolReply:
        message = self._request_message(messages, tools)
        try:
            return ToolReply.model_validate(message)
        except ValidationError as exc:
            raise ModelResponseError("模型工具响应格式无效") from exc

    def _request_message(
        self, messages: list[dict[str, str]], tools: list[dict[str, object]] | None = None
    ) -> dict[str, object]:
        payload: dict[str, object] = {"model": self.model_name, "messages": messages}
        if tools is not None:
            payload.update({"tools": tools, "tool_choice": "auto"})
        for attempt in range(2):
            try:
                response = self.http_client.post(
                    self.chat_url,
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json=payload,
                    timeout=10.0,
                )
                break
            except httpx.ConnectError as exc:
                if attempt == 1:
                    raise ModelConnectionError("模型连接失败") from exc
            except httpx.TimeoutException as exc:
                raise ModelTimeoutError("模型请求超时") from exc

        if response.status_code == 401:
            raise ModelAuthenticationError("模型接口鉴权失败")
        if response.is_error:
            raise ModelAPIError(response.status_code)
        try:
            message = response.json()["choices"][0]["message"]
        except (ValueError, KeyError, IndexError, TypeError) as exc:
            raise ModelResponseError("模型响应格式无效") from exc
        if not isinstance(message, dict):
            raise ModelResponseError("模型响应格式无效")
        return message


def create_model_client(
    settings: Settings,
    http_client: httpx.Client,
    fake_reply: str = "离线测试回答",
    fake_tool_reply: ToolReply | None = None,
) -> ModelClient:
    if settings.model_provider == "fake":
        return FakeModelClient(reply=fake_reply, tool_reply=fake_tool_reply)
    if settings.dashscope_api_key is None:
        raise ModelConfigurationError("千问模式需要 DASHSCOPE_API_KEY")
    api_key = settings.dashscope_api_key.get_secret_value()
    if not api_key.strip():
        raise ModelConfigurationError("千问模式需要 DASHSCOPE_API_KEY")
    return QwenModelClient(
        api_key=api_key,
        http_client=http_client,
        model_name=settings.model_name,
        base_url=settings.model_base_url,
    )
