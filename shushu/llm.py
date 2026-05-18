from __future__ import annotations

import json
import os
import re
from typing import Any

from .prompts import SYSTEM_PROMPT


DEFAULT_MODEL = "deepseek-chat"
DEFAULT_BASE_URL = "https://api.deepseek.com"


class LLMClient:
    def __init__(
        self,
        client: Any = None,
        model: str = DEFAULT_MODEL,
        base_url: str = DEFAULT_BASE_URL,
    ) -> None:
        if client is None:
            from openai import OpenAI

            api_key = os.environ.get("DEEPSEEK_API_KEY")
            if not api_key:
                raise RuntimeError("DEEPSEEK_API_KEY 未设置，无法调用 LLM。")
            client = OpenAI(api_key=api_key, base_url=base_url)
        self.client = client
        self.model = model

    def json_call(self, user_prompt: str, *, max_tokens: int = 4096) -> dict:
        resp = self.client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
        )
        text = _extract_text(resp)
        return _parse_json(text)


def _extract_text(resp: Any) -> str:
    choices = getattr(resp, "choices", None)
    if choices is None and isinstance(resp, dict):
        choices = resp.get("choices")
    if not choices:
        raise ValueError("LLM 返回缺少 choices 字段")
    first = choices[0]
    message = getattr(first, "message", None)
    if message is None and isinstance(first, dict):
        message = first.get("message")
    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    if content is None:
        raise ValueError("LLM 返回缺少 message.content")
    return str(content).strip()


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM 输出不是合法 JSON：{exc}\n原文：{text[:500]}") from exc
