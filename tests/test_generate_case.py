from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from shushu.generate_case import get_role, main, run_pipeline


def test_run_pipeline_returns_four_stages(fake_llm, sample_input_path):
    llm, fake = fake_llm
    role = get_role("ai_engineer")
    raw = sample_input_path.read_text(encoding="utf-8")

    stages = run_pipeline(raw, role, llm)

    assert set(stages) == {"extracted", "scan", "rewrite", "risk"}
    assert len(fake.calls) == 4
    assert stages["rewrite"]["resume_bullets"]
    assert stages["risk"]["follow_ups"]


def test_main_writes_tsx_and_raw(tmp_path, fake_llm, sample_input_path):
    llm, _ = fake_llm
    out_dir = tmp_path / "out"

    rc = main(
        [
            "--input",
            str(sample_input_path),
            "--target-role",
            "ai_engineer",
            "--out",
            str(out_dir) + "/",
        ],
        llm=llm,
    )

    assert rc == 0
    tsx = out_dir / "ai_engineer-sample-project.tsx"
    md = out_dir / "raw" / "ai_engineer-sample-project.md"
    assert tsx.exists()
    assert md.exists()

    tsx_text = tsx.read_text(encoding="utf-8")
    assert 'from "../PostShell"' in tsx_text
    assert "export const meta: PostMeta" in tsx_text
    assert "export default function" in tsx_text
    assert "ai_engineer-sample-project" in tsx_text or "sample-project" in tsx_text
    assert "[待补：" in tsx_text  # 没数字的地方必须保留待补标记


def test_unknown_role_raises(tmp_path, fake_llm, sample_input_path):
    llm, _ = fake_llm
    with pytest.raises(SystemExit):
        main(
            [
                "--input",
                str(sample_input_path),
                "--target-role",
                "no_such_role",
                "--out",
                str(tmp_path / "out") + "/",
            ],
            llm=llm,
        )


@pytest.mark.skipif(shutil.which("npx") is None, reason="npx unavailable")
def test_generated_tsx_parses_with_esbuild(tmp_path, fake_llm, sample_input_path):
    out_dir = tmp_path / "out"
    main(
        [
            "--input",
            str(sample_input_path),
            "--target-role",
            "ai_engineer",
            "--out",
            str(out_dir) + "/",
        ],
        llm=fake_llm[0],
    )
    tsx = next(out_dir.glob("*.tsx"))

    result = subprocess.run(
        [
            "npx",
            "--yes",
            "--package=esbuild@0.25.0",
            "esbuild",
            "--loader:.tsx=tsx",
            "--bundle=false",
            f"--outfile={tmp_path / 'discarded.js'}",
            str(tsx),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
