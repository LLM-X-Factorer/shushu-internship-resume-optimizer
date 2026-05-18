from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


class FakeAnthropicClient:
    """跑通流水线用的假 client。按 prompt 里出现的关键字返回固定 JSON。"""

    def __init__(self) -> None:
        self.messages = SimpleNamespace(create=self._create)
        self.calls: list[dict[str, Any]] = []

    def _create(self, *, model: str, max_tokens: int, system: Any, messages: list[dict[str, Any]]) -> Any:
        user_prompt = messages[0]["content"]
        self.calls.append({"model": model, "prompt": user_prompt})
        payload = self._route(user_prompt)
        text = json.dumps(payload, ensure_ascii=False)
        return SimpleNamespace(content=[SimpleNamespace(text=text)])

    def _route(self, prompt: str) -> dict[str, Any]:
        if "TASK_TAG: shushu.extract" in prompt:
            return {
                "background": "虚构票务平台想用 LLM 做客服工单的前置四分类。",
                "my_actions": [
                    "整理脱敏会话数据为训练 / 评测两个集合",
                    "设计最小 prompt 模板输出标签 + 理由",
                    "接 FastAPI 服务并在 Redis 做 30 分钟去重",
                ],
                "tech_details": [
                    "主模型 claude-sonnet，小模型兜底",
                    "FastAPI + Redis 服务",
                ],
                "results": ["[待补：准召数字]", "客服 leader 同意试点未上线"],
                "missing_info": ["真实 QPS / 延迟未测", "未做 A/B"],
            }
        if "TASK_TAG: shushu.scan" in prompt:
            return {
                "hits": [
                    {"skill_id": "llm", "evidence": "使用 claude-sonnet 做四分类", "strength": "strong"},
                    {"skill_id": "prompt_engineering", "evidence": "设计最小 prompt 模板", "strength": "medium"},
                    {"skill_id": "python", "evidence": "FastAPI 服务", "strength": "medium"},
                ],
                "misses": [
                    {"skill_id": "rag", "reason": "项目里没有检索增强"}
                ],
                "summary": "对 ai_engineer 角色契合度中等，证据偏 prompt 层。",
            }
        if "TASK_TAG: shushu.rewrite" in prompt:
            return {
                "review": {
                    "background": "虚构票务平台想做客服工单 LLM 前置四分类，背景是人工分流成本高。",
                    "my_actions": "整理脱敏数据、设计最小 prompt、接 FastAPI 服务、做评测脚本、和客服 leader 对账。",
                    "tech_details": "主路径 claude-sonnet，small 模型兜底，FastAPI + Redis 做 30 分钟去重，日志记录 token / 延迟 / 标签。",
                    "results": "评测集准确率 [待补：xx%]，未上线，客服 leader 同意小队试点。",
                },
                "resume_bullets": [
                    "搭建 FastAPI + LLM 客服工单四分类服务，准确率 [待补：xx%]",
                    "设计 prompt 模板与评测脚本，输出 [待补：xx 条] 抽样对照",
                ],
            }
        if "TASK_TAG: shushu.risk" in prompt:
            return {
                "follow_ups": [
                    {
                        "question": "评测准确率怎么算的？",
                        "why_asked": "判断你是否真的跑过评测",
                        "answer_skeleton": "先答抽样规模和分层方式，再补混淆矩阵口径，最后落到没做 A/B 的局限",
                    },
                    {
                        "question": "为什么不上线？",
                        "why_asked": "判断你对落地风险的判断",
                        "answer_skeleton": "先答试点范围，再补未测 QPS 的风险，最后落到客服 leader 的接受度门槛",
                    },
                ]
            }
        return {}


@pytest.fixture
def fake_llm():
    from shushu.llm import LLMClient

    fake = FakeAnthropicClient()
    return LLMClient(client=fake), fake


@pytest.fixture
def sample_input_path() -> Path:
    return FIXTURES / "sample_project.md"
