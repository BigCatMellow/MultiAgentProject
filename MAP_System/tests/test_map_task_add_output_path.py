#!/usr/bin/env python3
"""Tests for map_task.py add-output-path."""

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


def init_db(path: Path, status: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES ('codex', 'Codex', 'core', 'available')"
        )
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status, owner, attempt, max_attempts)
            VALUES ('TASK-001', 'TEST', 'Some task', 'desc', 'implementation', 'implementer', ?, 'codex', 0, 3)
            """,
            (status,),
        )
        conn.execute(
            "INSERT INTO task_output_paths (task_id, path) VALUES ('TASK-001', 'old.md')"
        )


def json_payload(stdout: str) -> dict:
    for line in reversed(stdout.splitlines()):
        if line.startswith("{"):
            return json.loads(line)
    raise AssertionError(f"no JSON payload in stdout: {stdout!r}")


def run_add_output_path(db: Path, out: Path | None = None) -> subprocess.CompletedProcess:
    args = [sys.executable, str(MAP_TASK), "--db", str(db)]
    if out is not None:
        args += ["--output-dir", str(out), "--event-log", str(out / "events" / "events.jsonl")]
    args += ["add-output-path", "TASK-001", "--path", "late.md", "--actor", "codex"]
    return subprocess.run(args, cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_add_output_path_succeeds_on_editable_task() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db, "READY")

        result = run_add_output_path(db, out)

        assert result.returncode == 0, result.stderr
        assert json_payload(result.stdout) == {"task_id": "TASK-001", "added": "late.md"}
        with sqlite3.connect(db) as conn:
            paths = {
                row[0]
                for row in conn.execute("SELECT path FROM task_output_paths WHERE task_id='TASK-001'")
            }
        assert paths == {"old.md", "late.md"}
        assert "registered late.md" in (out / "events" / "events.jsonl").read_text()


def test_add_output_path_rejects_released_task() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db, "RELEASED")

        result = run_add_output_path(db)

        assert result.returncode == 1
        assert "RELEASED" in result.stderr
        assert "not editable" in result.stderr
        with sqlite3.connect(db) as conn:
            paths = {
                row[0]
                for row in conn.execute("SELECT path FROM task_output_paths WHERE task_id='TASK-001'")
            }
        assert paths == {"old.md"}


def test_add_output_path_rejects_submitted_task() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db, "SUBMITTED")

        result = run_add_output_path(db)

        assert result.returncode == 1
        assert "not editable" in result.stderr


def main() -> int:
    for test in [
        test_add_output_path_succeeds_on_editable_task,
        test_add_output_path_rejects_released_task,
        test_add_output_path_rejects_submitted_task,
    ]:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
