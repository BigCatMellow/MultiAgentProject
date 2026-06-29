#!/usr/bin/env python3
"""Tests for scoped local Ollama helper runner."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts import local_runner


def fake_health(timeout: float) -> dict:
    return {
        "ollama": {
            "reachable": True,
            "models": [
                {"name": "llama3.2:3b", "available": True},
                {"name": "llama3.2:1b", "available": True},
            ],
        }
    }


def test_unknown_model_rejected() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "out.md"
        code = local_runner.main([
            "--task-id", "TASK-X",
            "--model", "unknown:model",
            "--scope", "test scope",
            "--prompt", "hello",
            "--output", str(output),
        ])
        assert code == 1
        assert not output.exists()


def test_output_note_and_event_written() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        output = base / "artifacts" / "out.md"
        events = base / "events.jsonl"
        helpers = base / "helpers"
        completed = subprocess.CompletedProcess(
            args=["ollama", "run", "llama3.2:3b"],
            returncode=0,
            stdout="model output\n",
            stderr="",
        )
        with mock.patch.object(local_runner, "build_report", side_effect=fake_health):
            with mock.patch.object(local_runner.subprocess, "run", return_value=completed) as run_mock:
                code = local_runner.main([
                    "--task-id", "TASK-X",
                    "--model", "llama3.2:3b",
                    "--scope", "summarize fixture",
                    "--prompt", "hello",
                    "--output", str(output),
                    "--event-log", str(events),
                    "--helper-dir", str(helpers),
                ])

        assert code == 0
        assert output.read_text(encoding="utf-8") == "model output\n"
        run_mock.assert_called_once()
        notes = list(helpers.glob("*.md"))
        assert len(notes) == 1
        note = notes[0].read_text(encoding="utf-8")
        assert "task_id: TASK-X" in note
        assert "model: llama3.2:3b" in note
        assert "scope: summarize fixture" in note
        assert f"output_path: {output}" in note
        event = json.loads(events.read_text(encoding="utf-8").strip())
        assert event["type"] == "HELPER_INVOKED"
        assert event["task_id"] == "TASK-X"
        assert str(output) in event["artifact_paths"]


def main() -> int:
    for test in [test_unknown_model_rejected, test_output_note_and_event_written]:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
