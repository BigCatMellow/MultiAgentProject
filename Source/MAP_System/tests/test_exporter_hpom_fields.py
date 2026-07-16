#!/usr/bin/env python3
"""Tests for preserving HPOM fields during SQLite-to-file export."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
EXPORTER = ROOT / "migration" / "export_to_files.py"


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript((ROOT / "migration" / "schema.sql").read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES ('codex-live', 'Codex Live', 'core', 'available')"
        )
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status, owner, attempt, max_attempts)
            VALUES
              ('TASK-H', 'TEST', 'Updated title', 'SQLite description', 'implementation',
               'implementer', 'SUBMITTED', 'codex-live', 0, 3)
            """
        )
        conn.execute(
            "INSERT INTO task_output_paths (task_id, path) VALUES ('TASK-H', 'MAP_System/example.py')"
        )
        conn.execute(
            "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES ('TASK-H', 'preserve HPOM fields')"
        )


def write_existing_task(out: Path) -> None:
    tasks = out / "tasks"
    tasks.mkdir(parents=True)
    (tasks / "TASK-H.json").write_text(
        json.dumps(
            {
                "task_id": "TASK-H",
                "title": "Old title",
                "task_type": "implementation",
                "role": "implementer",
                "status": "READY",
                "dependencies": [],
                "owner": "codex-live",
                "description": "Old description",
                "input_paths": ["MAP_System/shared/hpom.md"],
                "output_paths": [],
                "acceptance_criteria": [],
                "objective": "Preserve HPOM metadata through export.",
                "reviewer_role": "reviewer",
                "risk": "medium",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def test_hpom_fields_survive_export() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)
        write_existing_task(out)

        result = subprocess.run(
            [sys.executable, str(EXPORTER), "--db", str(db), "--output-dir", str(out)],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        assert result.returncode == 0, result.stderr

        payload = json.loads((out / "tasks" / "TASK-H.json").read_text(encoding="utf-8"))
        assert payload["title"] == "Updated title"
        assert payload["status"] == "SUBMITTED"
        assert payload["objective"] == "Preserve HPOM metadata through export."
        assert payload["reviewer_role"] == "reviewer"
        assert payload["risk"] == "medium"
        assert payload["input_paths"] == ["MAP_System/shared/hpom.md"]


def main() -> int:
    test_hpom_fields_survive_export()
    print("PASS test_hpom_fields_survive_export")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
