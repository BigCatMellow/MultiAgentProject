#!/usr/bin/env python3
"""Focused tests for validate_risk_registers.py."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
VALIDATOR = ROOT / "scripts" / "validate_risk_registers.py"
TEMPLATE = ROOT / "templates" / "RISK_REGISTER_TEMPLATE.md"


def copy_template(dst_root: Path) -> None:
    dst = dst_root / "templates"
    dst.mkdir(parents=True)
    shutil.copy2(TEMPLATE, dst / TEMPLATE.name)


def run_validator(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--root", str(root)],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_risk_validator_accepts_template_and_no_registers() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_template(root)

        result = run_validator(root)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS risk register validation" in result.stdout


def test_risk_validator_rejects_missing_template_fragment() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_template(root)
        template = root / "templates" / "RISK_REGISTER_TEMPLATE.md"
        template.write_text("# Risk Register Entry\nRisk ID: RISK-0001\n", encoding="utf-8")

        result = run_validator(root)

        assert result.returncode == 1
        assert "MISSING_FRAGMENT" in result.stdout
        assert "## Review history" in result.stdout


def test_risk_validator_rejects_register_placeholders() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_template(root)
        register = root / "shared" / "RISK_REGISTER.md"
        register.parent.mkdir(parents=True)
        register.write_text(
            "\n".join(
                [
                    "# Risk Register Entry",
                    "",
                    "Risk ID: RISK-0001",
                    "Project: MAP_System",
                    "Class: SECURITY",
                    "Severity: STRUCTURAL",
                    "Owner: codex-lab-test",
                    "Date opened: 2026-07-03",
                    "Last reviewed: 2026-07-03",
                    "Status: OPEN",
                    "",
                    "## Description",
                    "",
                    "<risk description>",
                    "",
                    "## Trigger / likelihood",
                    "",
                    "A security boundary is crossed without review.",
                    "",
                    "## Blast radius if realized",
                    "",
                    "Repo-level trust could be affected.",
                    "",
                    "## Current mitigation",
                    "",
                    "Security Second Pass.",
                    "",
                    "## Escalation",
                    "",
                    "- [x] SECURITY or STRUCTURAL - escalated to command-center: PENDING",
                    "",
                    "## Acceptance (if Status: ACCEPTED)",
                    "",
                    "- Decision class (per `DECISION_CLASSES.md`): NONE",
                    "- Approved by: NONE",
                    "- Linked decision: NONE",
                    "",
                    "## Review history",
                    "",
                    "| Date | Reviewed by | Notes |",
                    "|---|---|---|",
                    "| 2026-07-03 | codex-lab-test | opened |",
                    "",
                    "## Notes",
                    "",
                    "- none",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = run_validator(root)

        assert result.returncode == 1
        assert "REGISTER_PLACEHOLDER" in result.stdout
        assert "<risk description>" in result.stdout


def main() -> int:
    test_risk_validator_accepts_template_and_no_registers()
    print("PASS test_risk_validator_accepts_template_and_no_registers")
    test_risk_validator_rejects_missing_template_fragment()
    print("PASS test_risk_validator_rejects_missing_template_fragment")
    test_risk_validator_rejects_register_placeholders()
    print("PASS test_risk_validator_rejects_register_placeholders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
