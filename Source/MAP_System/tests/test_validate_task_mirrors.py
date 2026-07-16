#!/usr/bin/env python3
"""Tests for SQLite/file task mirror validation."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import importlib.util


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_task_mirrors.py"
SCHEMA = ROOT / "migration" / "schema.sql"
spec = importlib.util.spec_from_file_location("validate_task_mirrors", SCRIPT)
assert spec and spec.loader
validate_task_mirrors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_task_mirrors)


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES "
            "('codex-live', 'Codex Live', 'core', 'available')"
        )
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status,
               owner, attempt, max_attempts)
            VALUES
              ('TASK-M', 'TEST', 'Mirror task', 'desc', 'implementation',
               'worker', 'IN_PROGRESS', 'codex-live', 0, 3)
            """
        )
        conn.execute(
            "INSERT INTO task_output_paths (task_id, path) VALUES ('TASK-M', 'MAP_System/example.md')"
        )
        conn.execute(
            "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES ('TASK-M', 'mirrors match')"
        )


def mirror_payload(*, status: str = "IN_PROGRESS", output_paths: list[str] | None = None) -> dict:
    return {
        "task_id": "TASK-M",
        "title": "Mirror task",
        "task_type": "implementation",
        "role": "worker",
        "status": status,
        "dependencies": [],
        "owner": "codex-live",
        "description": "desc",
        "input_paths": [],
        "output_paths": output_paths if output_paths is not None else ["MAP_System/example.md"],
        "acceptance_criteria": ["mirrors match"],
    }


def write_mirrors(root: Path, *, status: str = "IN_PROGRESS", output_paths: list[str] | None = None) -> None:
    (root / "tasks").mkdir(parents=True)
    (root / "workflow").mkdir(parents=True)
    task = mirror_payload(status=status, output_paths=output_paths)
    (root / "tasks" / "TASK-M.json").write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
    graph_task = {
        key: task[key]
        for key in [
            "task_id",
            "title",
            "task_type",
            "role",
            "status",
            "dependencies",
            "owner",
            "output_paths",
            "acceptance_criteria",
        ]
    }
    (root / "workflow" / "task_graph.json").write_text(
        json.dumps({"project_id": "TEST", "tasks": [graph_task], "approval_gates": []}, indent=2) + "\n",
        encoding="utf-8",
    )


def test_matching_mirrors_pass() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)
        write_mirrors(out)

        assert validate_task_mirrors.validate(db, out) == []


def test_status_mismatch_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)
        write_mirrors(out, status="READY")

        errors = validate_task_mirrors.validate(db, out)

        assert any("status mismatch" in error for error in errors), errors


def test_output_path_mismatch_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)
        write_mirrors(out, output_paths=[])

        errors = validate_task_mirrors.validate(db, out)

        assert any("output_paths mismatch" in error for error in errors), errors


def main() -> int:
    for test in [
        test_matching_mirrors_pass,
        test_status_mismatch_fails,
        test_output_path_mismatch_fails,
    ]:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
