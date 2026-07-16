#!/usr/bin/env python3
"""Deterministic tests for the HPOM promotion gate."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.promote_task import promote_task  # noqa: E402


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript((ROOT / "migration" / "schema.sql").read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES ('codex-test', 'Codex Test', 'core', 'available')"
        )


def insert_task(
    db_path: Path,
    task_id: str,
    *,
    description: str = "Implement a checked task.",
    output_paths: tuple[str, ...] = ("scripts/example.py",),
    criteria: tuple[str, ...] = ("passes",),
    status: str = "NEEDS_SHAPING",
) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status, owner)
            VALUES (?, 'TEST', 'Test task', ?, 'implementation', 'implementer', ?, 'codex-test')
            """,
            (task_id, description, status),
        )
        for path in output_paths:
            conn.execute("INSERT INTO task_output_paths (task_id, path) VALUES (?, ?)", (task_id, path))
        for criterion in criteria:
            conn.execute(
                "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES (?, ?)",
                (task_id, criterion),
            )


def write_task_json(root: Path, task_id: str, **overrides: object) -> None:
    payload: dict[str, object] = {
        "task_id": task_id,
        "title": "Test task",
        "task_type": "implementation",
        "role": "implementer",
        "status": "NEEDS_SHAPING",
        "dependencies": [],
        "owner": "codex-test",
        "description": "Implement a checked task.",
        "objective": "Prove promotion works.",
        "required_context": ["MAP_System/shared/hpom.md"],
        "files_in_scope": ["scripts/example.py"],
        "forbidden_changes": ["Do not edit unrelated files."],
        "output_paths": ["scripts/example.py"],
        "acceptance_criteria": ["passes"],
        "expected_artifacts": ["artifacts/tests/example.md"],
        "reviewer_role": "reviewer",
        "risk": "low",
    }
    payload.update(overrides)
    tasks_dir = root / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    (tasks_dir / f"{task_id}.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def assert_status(db_path: Path, task_id: str, expected: str) -> None:
    with sqlite3.connect(db_path) as conn:
        row = conn.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
    assert row is not None
    assert row[0] == expected


def test_valid_task_promotes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db_path = root / "map.db"
        init_db(db_path)
        insert_task(db_path, "TASK-900")
        write_task_json(root, "TASK-900")

        result = promote_task("TASK-900", db_path=db_path, root=root, sync=False)

        assert result.ok, result.missing
        assert_status(db_path, "TASK-900", "READY")


def test_invalid_task_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db_path = root / "map.db"
        init_db(db_path)
        insert_task(db_path, "TASK-901")
        write_task_json(root, "TASK-901", reviewer_role="")

        result = promote_task("TASK-901", db_path=db_path, root=root, sync=False)

        assert not result.ok
        assert "json.reviewer_role" in result.missing
        assert_status(db_path, "TASK-901", "NEEDS_SHAPING")


def test_cli_error_names_missing_field() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db_path = root / "map.db"
        init_db(db_path)
        insert_task(db_path, "TASK-902", criteria=())
        write_task_json(root, "TASK-902", reviewer_role="")

        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "promote_task.py"),
                "--db",
                str(db_path),
                "--root",
                str(root),
                "--task-id",
                "TASK-902",
                "--no-sync",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        assert result.returncode == 1
        assert "json.reviewer_role" in result.stderr
        assert "sqlite.acceptance_criteria" in result.stderr
        assert_status(db_path, "TASK-902", "NEEDS_SHAPING")


def test_conflict_task_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        db_path = root / "map.db"
        init_db(db_path)
        insert_task(db_path, "TASK-903", status="CONFLICT")
        write_task_json(root, "TASK-903")

        try:
            promote_task("TASK-903", db_path=db_path, root=root, sync=False)
            raise AssertionError("expected PromoteError for CONFLICT task")
        except Exception as exc:
            assert "CONFLICT" in str(exc), f"unexpected error: {exc}"
        assert_status(db_path, "TASK-903", "CONFLICT")


def main() -> int:
    tests = [
        test_valid_task_promotes,
        test_invalid_task_blocked,
        test_cli_error_names_missing_field,
        test_conflict_task_blocked,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
