from pathlib import Path

import pytest

from shushu_internship_tool.achievement_audit import audit_sources, parse_sources, validate_sources, write_audit_outputs
from shushu_internship_tool.common import load_json


def test_achievement_audit_merges_multi_source_evidence(tmp_path: Path) -> None:
    fixture = Path(__file__).parent / "fixtures" / "intern_materials"
    payload = load_json(fixture / "sources.json")
    sources = parse_sources(payload)
    repo_root = Path(__file__).resolve().parent.parent
    for item in sources:
        path = Path(item["path_or_text"])
        if not path.is_absolute():
            item["path_or_text"] = str((repo_root / item["path_or_text"]).resolve())

    audit = audit_sources(sources, name="internship-materials")

    assert audit["source_count"] == 3
    assert "basic_rag" in audit["knowledge_modes"]
    assert any(item["resume_ready"] for item in audit["achievements"])
    assert any("缺少代码证据" not in item["risk_flags"] for item in audit["achievements"])
    assert any("business_docs" in item["source_types"] and "project_summary" in item["source_types"] for item in audit["achievements"])
    assert all("readiness_reason" in item for item in audit["achievements"])
    assert all("gaps" in item for item in audit["achievements"])

    paths = write_audit_outputs(audit, tmp_path)
    for path in paths.values():
        assert Path(path).exists()

    overview = Path(paths["overview_md"]).read_text(encoding="utf-8")
    business_rewrite = Path(paths["business_context_rewrite_md"]).read_text(encoding="utf-8")
    assert "成果审计报告" in overview
    assert "ticket" in overview.lower()
    assert "业务背景改写" in business_rewrite


def test_achievement_audit_splits_realistic_project_summary(tmp_path: Path) -> None:
    summary = tmp_path / "autoeval.md"
    summary.write_text(
        "\n".join(
            [
                "一句话定位",
                "GUI Agent 操作轨迹自动评估系统，用 LLM + 规则 + VLM 替代人工标注。",
                "核心问题",
                "人工标注成本高、周期长、一致性差，需要自动化方案。",
                "核心职责（STAR 法则，按亮点排序）",
                "1. 无效数据检测体系设计（P-E-R 流水线）",
                "设计 P-E-R 三阶段无效数据检测流水线，减少约 15% 无效 LLM 调用。",
                "2. LLM-as-Judge 评估 Prompt 工程",
                "设计三层判断结构 Prompt，评估 F1 达 88.9%，Recall 97%。",
                "3. 异步评估服务工程化",
                "基于 FastAPI + asyncio 构建异步评估服务，并增加 30s 防抖确认窗口。",
                "技术栈",
                "Python / FastAPI / asyncio / SQLite / LLM API",
            ]
        ),
        encoding="utf-8",
    )
    audit = audit_sources(
        [
            {
                "source_type": "project_summary",
                "title": "autoeval-summary",
                "path_or_text": str(summary),
            }
        ],
        name="autoeval",
    )

    titles = [item["title"] for item in audit["achievements"]]
    assert len(audit["achievements"]) >= 3
    assert any("无效数据检测" in title for title in titles)
    assert any("Prompt" in title or "评估" in title for title in titles)
    assert any(item["business_context"] for item in audit["achievements"])
    assert all("仅基于自述材料" in item["risk_flags"] for item in audit["achievements"])
    assert any(item["user_check_flags"] for item in audit["achievements"])
    assert any(
        "AI总结味较重，需人工核对" in item["user_check_flags"] or "存在可能夸大表述，需确认边界" in item["user_check_flags"]
        for item in audit["achievements"]
    )

    paths = write_audit_outputs(audit, tmp_path / "out")
    business_rewrite = Path(paths["business_context_rewrite_md"]).read_text(encoding="utf-8")
    assert "业务背景改写" in business_rewrite
    assert "自动化" in business_rewrite or "人工审核" in business_rewrite


def test_validate_sources_rejects_invalid_source_type() -> None:
    with pytest.raises(ValueError):
        validate_sources([{"source_type": "unknown", "path_or_text": "demo"}])
