#!/usr/bin/env python3
"""Tests for MAP event-log validation."""

from __future__ import annotations

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


def main() -> int:
    test_validate_events_warns_on_legacy_shape()
    print("PASS test_validate_events_warns_on_legacy_shape")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
