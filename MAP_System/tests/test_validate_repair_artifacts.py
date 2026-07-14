#!/usr/bin/env python3
"""Focused tests for validate_repair_artifacts.py."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
VALIDATOR = ROOT / "scripts" / "validate_repair_artifacts.py"
TEMPLATES = ROOT / "templates" / "repairs"


def copy_templates(dst_root: Path) -> None:
    dst = dst_root / "templates" / "repairs"
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


def test_repair_validator_accepts_templates_and_no_artifacts() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_templates(root)

        result = run_validator(root)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS repair validation" in result.stdout


def test_repair_validator_rejects_missing_template_fragment() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_templates(root)
        repair_template = root / "templates" / "repairs" / "REPAIR_RECORD_TEMPLATE.md"
        repair_template.write_text("# Repair Record\nRepair ID: REPAIR-0001\n", encoding="utf-8")

        result = run_validator(root)

        assert result.returncode == 1
        assert "MISSING_FRAGMENT" in result.stdout
        assert "## Verification" in result.stdout


def test_repair_validator_rejects_applied_record_placeholders() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_templates(root)
        repair_dir = root / "repairs"
        repair_dir.mkdir(parents=True)
        repair = repair_dir / "REPAIR-0001-placeholder.md"
        repair.write_text(
            "\n".join(
                [
                    "# Repair Record",
                    "Repair ID: REPAIR-0001",
                    "Related task: TASK-000",
                    "Found by: codex-lab-test",
                    "Date: 2026-07-03",
                    "Severity: DRIFT",
                    "Status: APPLIED",
                    "",
                    "## What was found",
                    "<finding>",
                    "",
                    "## Surfaced by",
                    "manual test",
                    "",
                    "## Severity rationale",
                    "mechanical drift",
                    "",
                    "## Proposed or applied fix",
                    "<fix>",
                    "",
                    "## Authority check",
                    "- [x] DRIFT or mechanical BLOCKING",
                    "",
                    "## Verification",
                    "validator passed",
                    "",
                    "## Recurrence check",
                    "- [x] First occurrence",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = run_validator(root)

        assert result.returncode == 1
        assert "FINAL_PLACEHOLDER" in result.stdout
        assert "<fix>" in result.stdout


def main() -> int:
    test_repair_validator_accepts_templates_and_no_artifacts()
    print("PASS test_repair_validator_accepts_templates_and_no_artifacts")
    test_repair_validator_rejects_missing_template_fragment()
    print("PASS test_repair_validator_rejects_missing_template_fragment")
    test_repair_validator_rejects_applied_record_placeholders()
    print("PASS test_repair_validator_rejects_applied_record_placeholders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
