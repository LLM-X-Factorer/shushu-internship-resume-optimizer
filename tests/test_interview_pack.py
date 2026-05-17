from pathlib import Path

from shushu_internship_tool.achievement_audit import audit_sources, parse_sources
from shushu_internship_tool.common import load_json
from shushu_internship_tool.interview_pack import write_interview_pack


def test_interview_pack_references_business_context(tmp_path: Path) -> None:
    fixture = Path(__file__).parent / "fixtures" / "intern_materials"
    payload = load_json(fixture / "sources.json")
    sources = parse_sources(payload)
    repo_root = Path(__file__).resolve().parent.parent
    for item in sources:
        item["path_or_text"] = str((repo_root / item["path_or_text"]).resolve())

    audit = audit_sources(sources, name="internship-materials")
    paths = write_interview_pack(audit, tmp_path, target_role="后端开发")

    qa_text = Path(paths["interview_qa"]).read_text(encoding="utf-8")
    star_text = Path(paths["resume_star"]).read_text(encoding="utf-8")
    risk_text = Path(paths["risk_answers"]).read_text(encoding="utf-8")
    intro_text = Path(paths["project_intro"]).read_text(encoding="utf-8")

    assert "业务" in qa_text or "上下游" in qa_text
    assert "Situation" in star_text
    assert "稳妥说法" in risk_text
    assert "需要优先核对" in qa_text
    assert "我主要参与了" not in intro_text
    assert "这个项目整体是在做" in intro_text
    assert "我主要负责其中几块" in intro_text
    assert intro_text.count("这个项目整体是在做") == 1
    assert Path(paths["interview_pack_json"]).exists()
