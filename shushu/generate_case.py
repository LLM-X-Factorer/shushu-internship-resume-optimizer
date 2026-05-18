from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from .common import ensure_dir, load_json, slugify, write_text
from .llm import LLMClient
from .prompts import extract_prompt, rewrite_prompt, risk_prompt, scan_prompt
from .render import render_raw_md, render_tsx


ROLES_PATH = Path(__file__).parent / "data" / "aijobfit_roles.json"


def load_roles() -> list[dict[str, Any]]:
    return load_json(ROLES_PATH)["roles"]


def get_role(role_id: str) -> dict[str, Any]:
    for role in load_roles():
        if role["role_id"] == role_id:
            return role
    available = ", ".join(r["role_id"] for r in load_roles())
    raise SystemExit(f"未知 target-role={role_id}，可用：{available}")


def run_pipeline(
    raw_input: str,
    role: dict[str, Any],
    llm: LLMClient,
) -> dict[str, dict[str, Any]]:
    extracted = llm.json_call(extract_prompt(raw_input))
    scan = llm.json_call(scan_prompt(extracted, role))
    rewrite = llm.json_call(rewrite_prompt(extracted, scan, role))
    risk = llm.json_call(risk_prompt(extracted, rewrite, role))
    return {"extracted": extracted, "scan": scan, "rewrite": rewrite, "risk": risk}


def derive_slug(input_path: Path, override: str | None) -> str:
    return slugify(override or input_path.stem)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="shushu-generate-case",
        description="把脱敏后的实习项目描述渲染成 aijobfit 应届分支可直接 import 的 .tsx 示范案例。",
    )
    parser.add_argument("--input", required=True, help="脱敏后的项目描述 .md")
    parser.add_argument(
        "--target-role",
        required=True,
        help="aijobfit 14 角色之一（见 shushu/data/aijobfit_roles.json）",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="输出 .tsx 文件路径；同名 .md 副本写到 <out 目录>/raw/",
    )
    parser.add_argument(
        "--slug",
        default=None,
        help="覆盖默认 slug（默认取 --input 文件名）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None, *, llm: LLMClient | None = None) -> int:
    args = parse_args(argv)

    input_path = Path(args.input)
    raw_input = input_path.read_text(encoding="utf-8")

    role = get_role(args.target_role)
    slug = derive_slug(input_path, args.slug)

    out_path = Path(args.out)
    if out_path.is_dir() or args.out.endswith("/"):
        out_path = out_path / f"{role['role_id']}-{slug}.tsx"
    ensure_dir(out_path.parent)

    llm = llm or LLMClient()
    stages = run_pipeline(raw_input, role, llm)

    tsx = render_tsx(role=role, slug=slug, **stages)
    write_text(out_path, tsx)

    raw_dir = ensure_dir(out_path.parent / "raw")
    raw_path = raw_dir / f"{role['role_id']}-{slug}.md"
    write_text(raw_path, render_raw_md(role=role, slug=slug, **stages))

    print(f"wrote {out_path}", file=sys.stderr)
    print(f"wrote {raw_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
