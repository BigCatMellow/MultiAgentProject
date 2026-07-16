#!/usr/bin/env python3
"""Regression tests for SQLite-to-file export invariants."""

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
SCHEMA = ROOT / "migration" / "schema.sql"


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.executemany(
            """
            INSERT INTO agents (agent_id, label, agent_type, status, reason)
            VALUES (?, ?, ?, ?, ?)
            """,
            [
                ("codex-live", "Codex Live", "core", "available", None),
                ("historical-agent", "Historical Agent", "core", "inactive", "session_ended"),
                ("limit-watcher", "Limit Watcher", "system", "inactive", "tool_identity"),
                ("map-task", "Map Task", "core", "inactive", "tool_identity"),
            ],
        )
        conn.executemany(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status,
               owner, attempt, max_attempts)
            VALUES (?, 'TEST', ?, ?, 'maintenance', 'implementer', ?, ?, 0, 3)
            """,
            [
                ("TASK-A", "Submitted task", "Needs review", "SUBMITTED", "codex-live"),
                ("TASK-B", "Retired duplicate", "Duplicate card", "RETIRED", "historical-agent"),
            ],
        )
        conn.executemany(
            "INSERT INTO task_output_paths (task_id, path) VALUES (?, ?)",
            [
                ("TASK-A", "MAP_System/example-a.py"),
                ("TASK-B", "MAP_System/example-b.py"),
            ],
        )
        conn.executemany(
            "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES (?, ?)",
            [
                ("TASK-A", "status mirrors sqlite"),
                ("TASK-B", "retired status mirrors sqlite"),
            ],
        )


def write_existing_files(out: Path) -> None:
    (out / "workflow").mkdir(parents=True)
    (out / "agents").mkdir(parents=True)
    (out / "workflow" / "task_graph.json").write_text(
        json.dumps({"project_id": "TEST", "tasks": [], "approval_gates": []}) + "\n",
        encoding="utf-8",
    )
    (out / "agents" / "status.json").write_text(
        json.dumps(
            {
                "agents": {
                    "codex-live": {"status": "available", "reason": None, "notes": "keep"},
                    "historical-agent": {
                        "status": "inactive",
                        "reason": "session_ended",
                        "notes": "old",
                    },
                    "map-task": {
                        "status": "inactive",
                        "reason": "tool_identity",
                        "notes": "tool",
                    },
                }
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def run_export(db: Path, out: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(EXPORTER), "--db", str(db), "--output-dir", str(out)],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_task_statuses_match_sqlite_in_task_files_and_graph() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)
        write_existing_files(out)
        run_export(db, out)

        task_a = json.loads((out / "tasks" / "TASK-A.json").read_text(encoding="utf-8"))
        task_b = json.loads((out / "tasks" / "TASK-B.json").read_text(encoding="utf-8"))
        graph = json.loads((out / "workflow" / "task_graph.json").read_text(encoding="utf-8"))
        graph_status = {task["task_id"]: task["status"] for task in graph["tasks"]}

        assert task_a["status"] == "SUBMITTED"
        assert task_b["status"] == "RETIRED"
        assert graph_status["TASK-A"] == "SUBMITTED"
        assert graph_status["TASK-B"] == "RETIRED"


def test_agent_status_export_is_filtered_operational_view() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)
        write_existing_files(out)
        run_export(db, out)

        agents = json.loads((out / "agents" / "status.json").read_text(encoding="utf-8"))["agents"]

        assert "codex-live" in agents
        assert agents["codex-live"]["notes"] == "keep"
        assert "historical-agent" not in agents  # inactive historical identity
        assert "limit-watcher" not in agents  # system/tool identity
        assert "map-task" not in agents  # inactive tool identity with no active task role


def main() -> int:
    test_task_statuses_match_sqlite_in_task_files_and_graph()
    print("PASS test_task_statuses_match_sqlite_in_task_files_and_graph")
    test_agent_status_export_is_filtered_operational_view()
    print("PASS test_agent_status_export_is_filtered_operational_view")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
