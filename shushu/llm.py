from __future__ import annotations

import json
import os
import re
from typing import Any

from .prompts import SYSTEM_PROMPT


DEFAULT_MODEL = "claude-sonnet-4-6"


class LLMClient:
    def __init__(self, client: Any = None, model: str = DEFAULT_MODEL) -> None:
        if client is None:
            import anthropic

            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise RuntimeError("ANTHROPIC_API_KEY 未设置，无法调用 LLM。")
            client = anthropic.Anthropic(api_key=api_key)
        self.client = client
        self.model = model

    def json_call(self, user_prompt: str, *, max_tokens: int = 4096) -> dict:
        resp = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = _extract_text(resp)
        return _parse_json(text)


def _extract_text(resp: Any) -> str:
    content = getattr(resp, "content", None)
    if content is None and isinstance(resp, dict):
        content = resp.get("content")
    if content is None:
        raise ValueError("LLM 返回缺少 content 字段")
    parts = []
    for block in content:
        text = getattr(block, "text", None)
        if text is None and isinstance(block, dict):
            text = block.get("text")
        if text:
            parts.append(text)
    return "".join(parts).strip()


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM 输出不是合法 JSON：{exc}\n原文：{text[:500]}") from exc
