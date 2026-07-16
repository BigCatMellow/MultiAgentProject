#!/usr/bin/env python3
"""Tests for map_task.py rework and create-time review warnings."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
MAP_TASK = ROOT / "scripts" / "map_task.py"
SCHEMA = ROOT / "migration" / "schema.sql"


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES ('codex', 'Codex', 'core', 'available')"
        )
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status, owner, attempt, max_attempts)
            VALUES ('TASK-001', 'TEST', 'Needs work', 'desc', 'implementation', 'implementer', 'CHANGES_REQUESTED', 'codex', 0, 3)
            """
        )
        conn.execute(
            "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES ('TASK-001', 'fix it')"
        )
        conn.execute(
            "INSERT INTO task_output_paths (task_id, path) VALUES ('TASK-001', 'out.md')"
        )


def json_payload(stdout: str) -> dict:
    for line in reversed(stdout.splitlines()):
        if line.startswith("{"):
            return json.loads(line)
    raise AssertionError(f"no JSON payload in stdout: {stdout!r}")


def test_rework_moves_changes_requested_to_ready() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)

        result = subprocess.run(
            [
                sys.executable, str(MAP_TASK),
                "--db", str(db),
                "--output-dir", str(out),
                "--event-log", str(out / "events" / "events.jsonl"),
                "rework", "TASK-001",
                "--actor", "codex",
                "--reason", "address review",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        assert result.returncode == 0, result.stderr
        assert json_payload(result.stdout) == {"task_id": "TASK-001", "status": "READY"}
        with sqlite3.connect(db) as conn:
            row = conn.execute("SELECT status, claimed_by FROM tasks WHERE task_id='TASK-001'").fetchone()
        assert row == ("READY", None)
        assert "returned to READY for rework" in (out / "events" / "events.jsonl").read_text()


def test_rework_rejects_wrong_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db)
        with sqlite3.connect(db) as conn:
            conn.execute("UPDATE tasks SET status='SUBMITTED' WHERE task_id='TASK-001'")

        result = subprocess.run(
            [
                sys.executable, str(MAP_TASK),
                "--db", str(db),
                "rework", "TASK-001",
                "--actor", "codex",
                "--reason", "address review",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        assert result.returncode == 1
        assert "not CHANGES_REQUESTED" in result.stderr


def test_create_warns_on_self_review_shape() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)

        result = subprocess.run(
            [
                sys.executable, str(MAP_TASK),
                "--db", str(db),
                "--output-dir", str(out),
                "--event-log", str(out / "events" / "events.jsonl"),
                "create",
                "--task-id", "TASK-002",
                "--title", "Review own work",
                "--owner", "codex",
                "--actor", "codex",
                "--task-type", "review",
                "--role", "reviewer",
                "--description", "desc",
                "--output-path", "review.md",
                "--criterion", "reviewed",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        assert result.returncode == 0, result.stderr
        assert "claim gate will block self-review claims" in result.stderr


def main() -> int:
    for test in [
        test_rework_moves_changes_requested_to_ready,
        test_rework_rejects_wrong_state,
        test_create_warns_on_self_review_shape,
    ]:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
