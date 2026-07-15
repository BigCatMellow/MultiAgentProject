#!/usr/bin/env python3
"""Focused tests for report-only decision conflict detection."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCRIPT = ROOT / "scripts" / "validate_decisions.py"


def run_validator(text: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "decisions.md"
        path.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--decisions-file", str(path)],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


def valid_decision(dec_id: str, title: str, applies_to: str, extra: str = "") -> str:
    return f"""## {dec_id}: {title}

Status: approved
Owner: command-center
Date: 2026-07-15
Applies-To: {applies_to}
{extra}
The decision body provides the required reason.
"""


def test_report_only_notes_for_dangling_and_one_way_supersession() -> None:
    text = (
        valid_decision("DEC-001", "Old route", "repo layout and git operations", "Superseded-By: DEC-002\n")
        + "\n"
        + valid_decision("DEC-002", "New route", "repo layout and git operations")
        + "\n"
        + valid_decision("DEC-003", "Removed route", "local helper scheduling", "Supersedes: DEC-999\n")
    )

    result = run_validator(text)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "SUPERSESSION_ONE_WAY: DEC-001 superseded_by DEC-002" in result.stdout
    assert "SUPERSESSION_DANGLING: DEC-003 supersedes unknown DEC-999" in result.stdout
    assert "2 report-only conflict note(s)" in result.stdout


def test_same_subject_pair_without_supersession_is_report_only() -> None:
    text = (
        valid_decision("DEC-010", "First repo policy", "repo layout and git operations")
        + "\n"
        + valid_decision("DEC-011", "Second repo policy", "repo layout, git operations, command center")
    )

    result = run_validator(text)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "POSSIBLE_DECISION_CONFLICT: DEC-010 and DEC-011" in result.stdout
    assert "layout, operations, repo" in result.stdout
    assert "1 report-only conflict note(s)" in result.stdout


def test_reciprocal_supersession_suppresses_same_subject_note() -> None:
    text = (
        valid_decision("DEC-020", "Old helper policy", "helper review routing", "Superseded-By: DEC-021\n")
        + "\n"
        + valid_decision("DEC-021", "New helper policy", "helper review routing", "Supersedes: DEC-020\n")
    )

    result = run_validator(text)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "SUPERSESSION_" not in result.stdout
    assert "POSSIBLE_DECISION_CONFLICT" not in result.stdout
    assert "0 report-only conflict note(s)" in result.stdout


if __name__ == "__main__":
    tests = [
        test_report_only_notes_for_dangling_and_one_way_supersession,
        test_same_subject_pair_without_supersession_is_report_only,
        test_reciprocal_supersession_suppresses_same_subject_note,
    ]
    for test in tests:
        test()
    print(f"PASS {len(tests)} decision conflict tests")
