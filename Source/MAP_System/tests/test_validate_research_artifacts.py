#!/usr/bin/env python3
"""Focused tests for validate_research_artifacts.py."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
VALIDATOR = ROOT / "scripts" / "validate_research_artifacts.py"
TEMPLATES = ROOT / "templates" / "research"


def copy_templates(dst_root: Path) -> None:
    dst = dst_root / "templates" / "research"
    dst.mkdir(parents=True)
    for path in TEMPLATES.glob("*.md"):
        shutil.copy2(path, dst / path.name)


def run_validator(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--root", str(root)],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_research_validator_accepts_templates_and_no_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_templates(root)

        result = run_validator(root)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS research validation" in result.stdout


def test_research_validator_rejects_missing_template_fragment() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_templates(root)
        summary = root / "templates" / "research" / "RESEARCH_SUMMARY_TEMPLATE.md"
        summary.write_text("# Research Summary\nSummary ID: SUMMARY-0001\n", encoding="utf-8")

        result = run_validator(root)

        assert result.returncode == 1
        assert "MISSING_FRAGMENT" in result.stdout
        assert "## Downstream effect" in result.stdout


def test_research_validator_rejects_final_artifact_placeholders() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_templates(root)
        artifact_dir = root / "artifacts" / "research"
        artifact_dir.mkdir(parents=True)
        artifact = artifact_dir / "SUMMARY-0001-placeholder.md"
        artifact.write_text(
            "\n".join(
                [
                    "# Research Summary",
                    "Summary ID: SUMMARY-0001",
                    "Related brief: BRIEF-0001",
                    "Related claim matrix: CLAIM-MATRIX-0001",
                    "Related assumption register: ASSUMPTIONS-0001",
                    "Owner: codex-lab-test",
                    "Date: 2026-07-03",
                    "Status: FINAL",
                    "",
                    "## Question",
                    "<question>",
                    "",
                    "## Answer",
                    "<answer>",
                    "",
                    "## Confidence",
                    "- [x] LOW",
                    "",
                    "## Confidence decays after",
                    "not time-sensitive",
                    "",
                    "## Open questions",
                    "- none",
                    "",
                    "## Downstream effect",
                    "- [x] Informational only",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = run_validator(root)

        assert result.returncode == 1
        assert "FINAL_PLACEHOLDER" in result.stdout
        assert "<answer>" in result.stdout


def main() -> int:
    test_research_validator_accepts_templates_and_no_artifacts()
    print("PASS test_research_validator_accepts_templates_and_no_artifacts")
    test_research_validator_rejects_missing_template_fragment()
    print("PASS test_research_validator_rejects_missing_template_fragment")
    test_research_validator_rejects_final_artifact_placeholders()
    print("PASS test_research_validator_rejects_final_artifact_placeholders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
