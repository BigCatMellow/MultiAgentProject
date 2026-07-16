#!/usr/bin/env python3
"""Tests for automatic MAP task ID allocation."""

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
            VALUES ('TASK-009', 'TEST', 'Old', 'desc', 'implementation', 'implementer', 'DONE', 'codex', 0, 3)
            """
        )


def run_create(db: Path, out: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, str(MAP_TASK),
            "--db", str(db),
            "--output-dir", str(out),
            "--event-log", str(out / "events" / "events.jsonl"),
            "create",
            "--task-id", "auto",
            "--title", "Auto task",
            "--owner", "codex",
            "--description", "desc",
            "--output-path", "out.md",
            "--criterion", "works",
            "--actor", "codex",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def created_id(output: str) -> str:
    for line in reversed(output.splitlines()):
        if line.startswith("{"):
            return json.loads(line)["created"]
    raise AssertionError(f"no JSON create payload in stdout: {output!r}")


def test_auto_task_id_allocates_next_number() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)

        first = run_create(db, out)
        second = run_create(db, out)

        assert first.returncode == 0, first.stderr
        assert second.returncode == 0, second.stderr
        assert created_id(first.stdout) == "TASK-010"
        assert created_id(second.stdout) == "TASK-011"


def main() -> int:
    test_auto_task_id_allocates_next_number()
    print("PASS test_auto_task_id_allocates_next_number")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
