from pathlib import Path

from shushu_internship_tool.achievement_audit import audit_sources, parse_sources
from shushu_internship_tool.common import load_json
from shushu_internship_tool.resume_rank import (
    rank_achievements,
    render_markdown,
    render_resume_project_summary,
    write_ranking_outputs,
)
from shushu_internship_tool.resume_style_bench import (
    detect_generated_style_issues,
    get_style_benchmark,
)


def test_resume_rank_prioritizes_jd_match_and_style_track() -> None:
    fixture = Path(__file__).parent / "fixtures" / "intern_materials"
    payload = load_json(fixture / "sources.json")
    sources = parse_sources(payload)
    repo_root = Path(__file__).resolve().parent.parent
    for item in sources:
        item["path_or_text"] = str((repo_root / item["path_or_text"]).resolve())

    audit = audit_sources(sources, name="internship-materials")
    jd_text = (fixture / "target_jd.txt").read_text(encoding="utf-8")
    ranked = rank_achievements(jd_text, audit["achievements"], target_role="后端开发")

    assert ranked
    assert ranked[0]["score"] >= ranked[-1]["score"]
    assert "fastapi" in " ".join(ranked[0]["keywords_hit"]).lower() or "后端" in "".join(ranked[0]["keywords_hit"])
    assert ranked[0]["resume_bullets"][0]
    assert ranked[0]["recommendation_reason"]
    assert ranked[0]["next_steps"]

    benchmark = get_style_benchmark("算法 / AI")
    assert benchmark["track"] == "ai"


def test_resume_rank_writes_less_repetitive_bullet_for_autoeval_style_item() -> None:
    item = {
        "title": "无效数据检测流水线",
        "background": "人工标注成本高、周期长，需要自动化方案。",
        "task": "设计 P-E-R 三阶段无效数据检测流水线。",
        "actions": ["设计 P-E-R 三阶段无效数据检测流水线，减少约 15% 无效 LLM 调用。"],
        "business_context": "人工标注成本高、周期长、一致性差，需要自动化方案。",
        "metrics": ["减少约 15% 无效 LLM 调用"],
        "tech_stack": ["Python", "LLM", "VLM"],
        "evidence": [{"source_ref": "summary.md"}],
        "source_types": ["project_summary"],
        "resume_ready": True,
        "risk_flags": ["仅基于自述材料"],
        "user_check_flags": ["存在可能夸大表述，需确认边界"],
        "user_check_evidence": ["独立设计并实现基于 LLM 的系统"],
        "matched_keywords": ["agent", "workflow"],
    }
    ranked = rank_achievements("AI Agent workflow API 自动化", [item], target_role="AI应用工程")
    bullet_a, bullet_b = ranked[0]["resume_bullets"]
    assert "无效数据检测流水线" in bullet_a
    assert "减少约 15% 无效 LLM 调用" in bullet_a
    assert bullet_a.count("无效数据检测流水线") == 1
    assert "存在可能夸大表述，需确认边界" in ranked[0]["risk_notes"]
    assert bullet_a != bullet_b
    assert "..." not in bullet_a
    assert "..." not in bullet_b
    assert not (bullet_a.startswith("独立设计并实现") and bullet_b.startswith("独立设计并实现"))


def test_resume_rank_generates_project_specific_next_steps_and_resume_summary(tmp_path: Path) -> None:
    item = {
        "title": "GUI Agent 评估与错误标签归因",
        "background": "面向手机 GUI Agent 数据组，负责自动化打标相关 workflow。",
        "task": "优化任务完成自动评估，并对失败 case 做一级、二级标签归因。",
        "actions": [
            "通过 prompt 优化、无效数据处理提升任务完成判断准确率",
            "对失败 case 做一级、二级错误标签自动化判别",
            "基于 FastAPI 与 asyncio 搭建评估 workflow",
        ],
        "business_context": "服务 GUI Agent 数据闭环，降低人工评估与错误分析成本。",
        "metrics": [],
        "tech_stack": ["Python", "FastAPI", "asyncio", "LLM"],
        "evidence": [{"source_ref": "project_summary.md"}],
        "source_types": ["project_summary"],
        "resume_ready": False,
        "risk_flags": ["缺少代码证据"],
        "user_check_flags": ["AI总结味较重，需人工核对"],
        "user_check_evidence": ["全链路闭环"],
        "matched_keywords": ["eval", "workflow", "label", "Agent"],
    }

    ranked = rank_achievements("AI Agent eval workflow label attribution", [item], target_role="AI应用工程")
    next_steps = ranked[0]["next_steps"]
    joined = "\n".join(next_steps)
    assert "F1" in joined or "Recall" in joined or "Precision" in joined
    assert "一级/二级错误标签归因" in joined
    assert "workflow" in joined or "服务化" in joined
    assert "代码、PR 或服务实现证据" in joined

    summary = render_resume_project_summary(ranked, target_role="AI应用工程")
    assert "简历项目精简版" in summary
    assert "可直接写进简历" in summary
    assert ranked[0]["resume_bullets"][0] in summary
    assert "..." not in summary

    paths = write_ranking_outputs(ranked, tmp_path, target_role="AI应用工程")
    summary_path = Path(paths["resume_project_summary_md"])
    assert summary_path.exists()
    persisted = summary_path.read_text(encoding="utf-8")
    assert "简历项目精简版" in persisted
    assert "..." not in persisted


def test_generated_style_issue_detection_flags_mechanical_openers() -> None:
    bullets = [
        "独立设计并实现无效数据检测流水线，围绕评估流程改进规则策略",
        "独立设计并实现异步评估服务，围绕批处理任务完善并发控制",
        "独立设计并实现错误标签归因流程，围绕失败 case 完善标签体系",
    ]
    issues = detect_generated_style_issues(bullets)
    joined = "\n".join(issues)
    assert "机械重复开头" in joined
    assert "AI 味较重" in joined or "重复" in joined


def test_render_outputs_surface_generated_style_warning() -> None:
    item = {
        "title": "无效数据检测流水线",
        "background": "人工标注成本高、周期长，需要自动化方案。",
        "task": "设计无效数据检测与评估 workflow。",
        "actions": ["设计无效数据检测流水线，减少约 15% 无效 LLM 调用。"],
        "business_context": "服务 GUI Agent 自动评估闭环。",
        "metrics": ["减少约 15% 无效 LLM 调用"],
        "tech_stack": ["Python", "LLM"],
        "evidence": [{"source_ref": "summary.md"}],
        "source_types": ["project_summary"],
        "resume_ready": True,
        "risk_flags": [],
        "user_check_flags": [],
        "user_check_evidence": [],
        "matched_keywords": ["agent", "workflow"],
    }
    ranked = rank_achievements("AI Agent workflow", [item], target_role="AI应用工程")
    ranked = ranked * 4
    for index, ranked_item in enumerate(ranked):
        ranked_item["resume_bullets"] = [
            f"独立设计并实现无效数据检测流水线{index}，围绕评估流程改进规则策略",
            f"独立设计并实现异步评估服务{index}，围绕批处理任务完善并发控制",
        ]

    markdown = render_markdown(ranked, target_role="AI应用工程")
    summary = render_resume_project_summary(ranked, target_role="AI应用工程")
    assert "生成表述提醒" in markdown
    assert "机械重复开头" in markdown
    assert "生成表述提醒" in summary
