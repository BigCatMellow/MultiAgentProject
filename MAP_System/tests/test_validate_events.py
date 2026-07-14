#!/usr/bin/env python3
"""Tests for MAP event-log validation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCRIPT = ROOT / "scripts" / "validate_events.py"


def test_validate_events_warns_on_legacy_shape() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "events.jsonl"
        log.write_text(
            '{"timestamp":"2026-01-01T00:00:00Z","type":"task_progress","task_id":"TASK-1","agent":"codex","summary":"x","artifact_paths":[]}\n',
            encoding="utf-8",
        )
        loose = subprocess.run(
            [sys.executable, str(SCRIPT), "--event-log", str(log)],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        strict = subprocess.run(
            [sys.executable, str(SCRIPT), "--event-log", str(log), "--strict"],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert loose.returncode == 0, loose.stderr
        assert strict.returncode == 1
        assert "legacy timestamp" in loose.stdout


def test_fail_on_new_ignores_baseline_but_catches_fresh_warnings() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "events.jsonl"
        baseline = Path(tmp) / "warning_baseline.json"
        good_line = (
            '{"created_at":"2026-01-01T00:00:00Z","type":"PROGRESS","task_id":"TASK-1",'
            '"sender":"codex","summary":"x","artifact_paths":[]}\n'
        )
        legacy_bad_line = (
            '{"timestamp":"2026-01-01T00:00:00Z","type":"task_progress","task_id":"TASK-1",'
            '"agent":"codex","summary":"x","artifact_paths":[]}\n'
        )
        # Line 1 is a pre-existing legacy-shaped warning; line 2 is a fresh one appended later.
        log.write_text(legacy_bad_line + good_line + legacy_bad_line, encoding="utf-8")
        baseline.write_text(json.dumps({"baseline_line_count": 1}), encoding="utf-8")

        within_baseline = subprocess.run(
            [sys.executable, str(SCRIPT), "--event-log", str(log), "--warning-baseline", str(baseline)],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        fail_on_new = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--event-log",
                str(log),
                "--warning-baseline",
                str(baseline),
                "--fail-on-new",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert within_baseline.returncode == 0, within_baseline.stderr
        assert fail_on_new.returncode == 1
        assert "WARN-NEW" in fail_on_new.stdout
        assert "line 3" in fail_on_new.stdout


def test_trace_fields_absent_causes_no_warning() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "events.jsonl"
        log.write_text(
            '{"created_at":"2026-01-01T00:00:00Z","type":"PROGRESS","task_id":"TASK-1",'
            '"sender":"codex","summary":"x","artifact_paths":[]}\n',
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--event-log",
                str(log),
                "--warning-baseline",
                str(Path(tmp) / "no-baseline.json"),
                "--fail-on-new",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "trace" not in result.stdout


def test_trace_fields_present_and_well_formed_causes_no_warning() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "events.jsonl"
        log.write_text(
            '{"created_at":"2026-01-01T00:00:00Z","type":"PROGRESS","task_id":"TASK-1",'
            '"sender":"codex","summary":"x","artifact_paths":[],'
            '"trace_id":"trc-1","parent_event_id":"evt-0","actor":"codex",'
            '"action":"submit","target":"TASK-1","thread":"map-613"}\n',
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--event-log",
                str(log),
                "--warning-baseline",
                str(Path(tmp) / "no-baseline.json"),
                "--fail-on-new",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "trace" not in result.stdout


def test_task_trace_id_convention_causes_no_warning() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "events.jsonl"
        log.write_text(
            '{"created_at":"2026-01-01T00:00:00Z","type":"PROGRESS","task_id":"TASK-1",'
            '"sender":"codex","summary":"x","artifact_paths":[],'
            '"trace_id":"task:TASK-1","actor":"codex","action":"progress","target":"TASK-1"}\n',
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--event-log",
                str(log),
                "--warning-baseline",
                str(Path(tmp) / "no-baseline.json"),
                "--fail-on-new",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert "trace" not in result.stdout


def test_trace_field_malformed_when_present_is_new_warning() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "events.jsonl"
        log.write_text(
            '{"created_at":"2026-01-01T00:00:00Z","type":"PROGRESS","task_id":"TASK-1",'
            '"sender":"codex","summary":"x","artifact_paths":[],"trace_id":""}\n',
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--event-log",
                str(log),
                "--warning-baseline",
                str(Path(tmp) / "no-baseline.json"),
                "--fail-on-new",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert result.returncode == 1
        assert "trace field trace_id present but not a non-empty string" in result.stdout


def test_parent_event_id_without_trace_id_is_new_warning() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "events.jsonl"
        log.write_text(
            '{"created_at":"2026-01-01T00:00:00Z","type":"PROGRESS","task_id":"TASK-1",'
            '"sender":"codex","summary":"x","artifact_paths":[],"parent_event_id":"evt-0"}\n',
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--event-log",
                str(log),
                "--warning-baseline",
                str(Path(tmp) / "no-baseline.json"),
                "--fail-on-new",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert result.returncode == 1
        assert "parent_event_id present without trace_id" in result.stdout


def main() -> int:
    test_validate_events_warns_on_legacy_shape()
    print("PASS test_validate_events_warns_on_legacy_shape")
    test_fail_on_new_ignores_baseline_but_catches_fresh_warnings()
    print("PASS test_fail_on_new_ignores_baseline_but_catches_fresh_warnings")
    test_trace_fields_absent_causes_no_warning()
    print("PASS test_trace_fields_absent_causes_no_warning")
    test_trace_fields_present_and_well_formed_causes_no_warning()
    print("PASS test_trace_fields_present_and_well_formed_causes_no_warning")
    test_task_trace_id_convention_causes_no_warning()
    print("PASS test_task_trace_id_convention_causes_no_warning")
    test_trace_field_malformed_when_present_is_new_warning()
    print("PASS test_trace_field_malformed_when_present_is_new_warning")
    test_parent_event_id_without_trace_id_is_new_warning()
    print("PASS test_parent_event_id_without_trace_id_is_new_warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
