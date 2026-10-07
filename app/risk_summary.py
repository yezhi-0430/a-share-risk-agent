import json
from typing import Literal

from pydantic import BaseModel, ValidationError

from app.llm_client import ModelClient


class RiskSummaryParseError(Exception):
    pass


class RiskSummary(BaseModel):
    facts: list[str]
    inferences: list[str]
    unknowns: list[str]
    risk_level: Literal["low", "medium", "high", "unknown"]
    sources: list[str]


def parse_risk_summary(text: str) -> RiskSummary:
    try:
        return RiskSummary.model_validate_json(text)
    except ValidationError as exc:
        raise RiskSummaryParseError("模型输出格式无效") from exc


def generate_risk_summary(
    client: ModelClient,
    input_text: str,
) -> RiskSummary:
    schema = json.dumps(
        RiskSummary.model_json_schema(),
        ensure_ascii=False,
    )

    messages = [
        {
            "role": "system",
            "content": (
                "请根据用户提供的数据生成风险摘要。"
                "区分事实、推断和未知信息，不编造数据或来源。"
                "信息不足或没有明确评级依据时，risk_level 使用 unknown。"
                "只返回符合以下 JSON Schema 的 JSON 对象，"
                "不要添加 Markdown 代码块或额外说明：" + schema
            ),
        },
        {"role": "user", "content": input_text},
    ]

    reply = client.chat(messages)
    return parse_risk_summary(reply)
