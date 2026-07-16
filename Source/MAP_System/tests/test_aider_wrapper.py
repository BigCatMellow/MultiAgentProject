#!/usr/bin/env python3
"""Tests for supervised Aider setup wrapper."""

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

from MAP_System.scripts import aider_wrapper


def write_task(tasks_dir: Path) -> None:
    tasks_dir.mkdir(parents=True)
    (tasks_dir / "TASK-X.json").write_text(
        json.dumps(
            {
                "task_id": "TASK-X",
                "output_paths": [
                    "MAP_System/scripts/aider_wrapper.py",
                    "MAP_System/tests/test_aider_wrapper.py",
                ],
            }
        ),
        encoding="utf-8",
    )


def run_args(base: Path, *extra: str) -> list[str]:
    return [
        "--task-id", "TASK-X",
        "--intent", "test aider setup",
        "--target", "MAP_System/scripts/aider_wrapper.py",
        "--tasks-dir", str(base / "tasks"),
        "--helper-dir", str(base / "helpers"),
        "--event-log", str(base / "events.jsonl"),
        "--repo", str(base / "repo"),
        *extra,
    ]


def clean_git(*args, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=args, returncode=0, stdout="", stderr="")


def dirty_git(*args, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(
        args=args,
        returncode=0,
        stdout=" M MAP_System/scripts/aider_wrapper.py\n",
        stderr="",
    )


def test_out_of_scope_target_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        write_task(base / "tasks")
        with mock.patch.object(aider_wrapper.subprocess, "run", side_effect=clean_git):
            code = aider_wrapper.main([
                "--task-id", "TASK-X",
                "--intent", "test",
                "--target", "README.md",
                "--tasks-dir", str(base / "tasks"),
                "--helper-dir", str(base / "helpers"),
                "--event-log", str(base / "events.jsonl"),
                "--repo", str(base / "repo"),
                "--dry-run",
            ])
        assert code == 1
        assert not (base / "events.jsonl").exists()


def test_dirty_target_fails_before_note() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        write_task(base / "tasks")
        with mock.patch.object(aider_wrapper.subprocess, "run", side_effect=dirty_git):
            code = aider_wrapper.main([*run_args(base), "--dry-run"])
        assert code == 1
        assert not (base / "helpers").exists()


def test_helper_note_event_and_interactive_launch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        write_task(base / "tasks")
        with mock.patch.object(aider_wrapper.subprocess, "run", side_effect=clean_git):
            with mock.patch.object(aider_wrapper.subprocess, "call", return_value=0) as call_mock:
                code = aider_wrapper.main([*run_args(base), "--", "--model", "sonnet"])
        assert code == 0
        call_mock.assert_called_once()
        cmd = call_mock.call_args.args[0]
        assert cmd[0] == "aider"
        assert "--yes-always" not in cmd
        assert "MAP_System/scripts/aider_wrapper.py" in cmd
        notes = list((base / "helpers").glob("*.md"))
        assert len(notes) == 1
        note = notes[0].read_text(encoding="utf-8")
        assert "task_id: TASK-X" in note
        assert "test aider setup" in note
        event = json.loads((base / "events.jsonl").read_text(encoding="utf-8").strip())
        assert event["type"] == "HELPER_INVOKED"
        assert event["task_id"] == "TASK-X"


def test_forbidden_aider_flag_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        write_task(base / "tasks")
        with mock.patch.object(aider_wrapper.subprocess, "run", side_effect=clean_git):
            code = aider_wrapper.main([*run_args(base), "--", "--yes-always"])
        assert code == 1


def test_no_auto_commits_allowed() -> None:
    aider_wrapper.validate_aider_args(["--no-auto-commits"])
    try:
        aider_wrapper.validate_aider_args(["--auto-commits"])
        raise AssertionError("expected --auto-commits to remain forbidden")
    except aider_wrapper.AiderWrapperError:
        pass


def main() -> int:
    tests = [
        test_out_of_scope_target_fails,
        test_dirty_target_fails_before_note,
        test_helper_note_event_and_interactive_launch,
        test_forbidden_aider_flag_fails,
        test_no_auto_commits_allowed,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
