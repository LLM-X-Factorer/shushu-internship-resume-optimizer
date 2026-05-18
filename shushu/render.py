from __future__ import annotations

import json
import re
from datetime import date
from typing import Any


def _js_string(text: Any) -> str:
    """渲染成 JSX 表达式里可用的字符串字面量（含两端引号）。"""
    if text is None:
        return '""'
    return (
        '"'
        + str(text)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        + '"'
    )


def _jsx_text(text: Any) -> str:
    """渲染成 JSX 节点正文（包了一层 {"..."} 表达式，避免 { } 被解析）。"""
    return "{" + _js_string(text) + "}"


def _component_name(role_id: str, slug: str) -> str:
    parts = re.split(r"[^a-zA-Z0-9]+", f"{role_id}-{slug}")
    name = "".join(p[:1].upper() + p[1:] for p in parts if p)
    if not name or not name[0].isalpha():
        name = "Post" + name
    return name


def render_tsx(
    *,
    role: dict[str, Any],
    slug: str,
    extracted: dict[str, Any],
    scan: dict[str, Any],
    rewrite: dict[str, Any],
    risk: dict[str, Any],
    published_at: str | None = None,
) -> str:
    role_name = role["role_name"]
    role_id = role["role_id"]
    component = _component_name(role_id, slug)
    published_at = published_at or date.today().isoformat()

    background_preview = (rewrite.get("review", {}).get("background") or "").strip()
    title = f"{role_name}方向实习复盘示范 · {slug}"
    excerpt = background_preview[:160] or "应届实习复盘示范案例。"

    review = rewrite.get("review", {})
    bullets = rewrite.get("resume_bullets") or []
    hits = scan.get("hits") or []
    follow_ups = risk.get("follow_ups") or []
    missing = extracted.get("missing_info") or []

    hits_rows = []
    for h in hits[:10]:
        hits_rows.append(
            "          ["
            + ", ".join(
                [
                    _js_string(h.get("skill_id", "")),
                    _js_string(h.get("strength", "")),
                    _js_string(h.get("evidence", "")),
                ]
            )
            + "],"
        )
    hits_table = "\n".join(hits_rows) if hits_rows else "          []"

    bullets_li = "\n".join(
        f"        <Li>{_jsx_text(b)}</Li>" for b in bullets
    ) or "        <Li>{\"[待补：简历版 bullet]\"}</Li>"

    follow_blocks = []
    for fu in follow_ups:
        question = fu.get("question", "")
        why_asked = fu.get("why_asked", "")
        skeleton = fu.get("answer_skeleton", "")
        follow_blocks.append(
            "      <Callout tone=\"warn\" title={"
            + _js_string(f"追问：{question}")
            + "}>\n"
            + f"        <Strong>面试官为什么会问：</Strong>{_jsx_text(why_asked)}\n"
            + "        <br /><br />\n"
            + f"        <Strong>答法骨架：</Strong>{_jsx_text(skeleton)}\n"
            + "      </Callout>"
        )
    follow_section = "\n\n".join(follow_blocks) or "      <P>{\"[待补：面试追问点]\"}</P>"

    missing_li = "\n".join(
        f"        <Li>{_jsx_text(m)}</Li>" for m in missing
    ) or "        <Li>{\"[待补：原文缺失信息列表]\"}</Li>"

    return f"""import {{
  PostShell,
  H2,
  P,
  Ul,
  Li,
  Callout,
  DataTable,
  Strong,
  type PostMeta,
}} from "../PostShell";

export const meta: PostMeta = {{
  slug: {_js_string(slug)},
  title: {_js_string(title)},
  excerpt: {_js_string(excerpt)},
  publishedAt: {_js_string(published_at)},
  tags: [{_js_string('应届')}, {_js_string('实习复盘')}, {_js_string(role_name)}, {_js_string(role_id)}],
  readMinutes: 8,
}};

export default function {component}() {{
  return (
    <PostShell meta={{meta}}>
      <Callout tone="info" title={_js_string(f"目标角色：{role_name}（{role_id}）")}>
        {_jsx_text(scan.get('summary', '[待补：角色契合度一句话总结]'))}
      </Callout>

      <H2>业务背景</H2>
      <P>{_jsx_text(review.get('background', '[待补：背景描述]'))}</P>

      <H2>我做了什么</H2>
      <P>{_jsx_text(review.get('my_actions', '[待补：动作描述]'))}</P>

      <H2>技术细节</H2>
      <P>{_jsx_text(review.get('tech_details', '[待补：技术细节]'))}</P>

      <H2>结果</H2>
      <P>{_jsx_text(review.get('results', '[待补：结果描述]'))}</P>

      <H2>{_jsx_text(f"对照 {role_name} 角色的技能命中")}</H2>
      <DataTable
        headers={{[{_js_string('技能')}, {_js_string('强度')}, {_js_string('证据')}]}}
        rows={{[
{hits_table}
        ]}}
      />

      <H2>简历压缩版（直接抄）</H2>
      <Ul>
{bullets_li}
      </Ul>

      <H2>面试追问点 + 答法骨架</H2>
{follow_section}

      <H2>原文里没说清的事</H2>
      <Ul>
{missing_li}
      </Ul>
    </PostShell>
  );
}}
"""


def render_raw_md(
    *,
    role: dict[str, Any],
    slug: str,
    extracted: dict[str, Any],
    scan: dict[str, Any],
    rewrite: dict[str, Any],
    risk: dict[str, Any],
) -> str:
    sections = [
        f"# {role['role_name']}（{role['role_id']}）· {slug}",
        "",
        "## 1. 抽取",
        "```json",
        json.dumps(extracted, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 2. 命中扫描",
        "```json",
        json.dumps(scan, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 3. 改写",
        "```json",
        json.dumps(rewrite, ensure_ascii=False, indent=2),
        "```",
        "",
        "## 4. 面试追问",
        "```json",
        json.dumps(risk, ensure_ascii=False, indent=2),
        "```",
        "",
    ]
    return "\n".join(sections)
