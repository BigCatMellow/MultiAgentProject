#!/usr/bin/env python3
"""Regression test for stable multi-gate approval resume ordering."""

from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

from langgraph.types import Command

ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from MAP_System.db.checkpointer import MapSqliteSaver  # noqa: E402
from MAP_System.graph.runner import build_graph  # noqa: E402

SCHEMA = ROOT / "migration" / "schema.sql"
RUNTIME_POLICY = ROOT / "workflow" / "runtime_policy.yaml"
TASK_GRAPH = ROOT / "workflow" / "task_graph.json"


def create_temp_db(tmp: Path) -> Path:
    db = tmp / "multigate.db"
    with sqlite3.connect(db) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES (?,?,?,?)",
            ("test-agent", "Test Agent", "core", "available"),
        )
        conn.execute(
            """INSERT INTO tasks
               (task_id, project_id, title, description, task_type, role, status,
                priority, owner, attempt, max_attempts)
               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
            (
                "TASK-GATE-SEED",
                "TEST-PROJECT",
                "Gate seed task",
                "Seed task for approval gate fixture",
                "implementation",
                "implementer",
                "APPROVED",
                1,
                "test-agent",
                1,
                3,
            ),
        )
        conn.execute(
            """INSERT INTO approval_gates
               (gate_id, name, required_after_task, status)
               VALUES (?,?,?,?)""",
            ("GATE-A", "First gate", "TASK-GATE-SEED", "pending"),
        )
        conn.execute(
            """INSERT INTO approval_gates
               (gate_id, name, required_after_task, status)
               VALUES (?,?,?,?)""",
            ("GATE-B", "Second gate", "TASK-GATE-SEED", "pending"),
        )
    return db


def assert_interrupted(result: dict, label: str) -> None:
    if not result.get("__interrupt__"):
        raise AssertionError(f"{label}: expected graph interrupt, got {result!r}")


def gate_statuses(db: Path) -> list[tuple[str, str]]:
    with sqlite3.connect(db) as conn:
        return conn.execute(
            "SELECT gate_id, status FROM approval_gates ORDER BY rowid"
        ).fetchall()


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="map_multigate_"))
    try:
        db = create_temp_db(tmp)
        app = build_graph(checkpointer=MapSqliteSaver(db))
        cfg = {"configurable": {"thread_id": "multigate-regression"}}

        first = app.invoke(
            {
                "graph_path": str(TASK_GRAPH),
                "runtime_policy_path": str(RUNTIME_POLICY),
                "db_path": str(db),
                "events": [],
            },
            cfg,
        )
        assert_interrupted(first, "initial run")

        second = app.invoke(Command(resume={"gate_id": "GATE-A", "approved": True}), cfg)
        assert_interrupted(second, "after approving GATE-A")

        third = app.invoke(Command(resume={"gate_id": "GATE-B", "approved": False}), cfg)
        if third.get("__interrupt__"):
            raise AssertionError(f"final resume should not interrupt, got {third!r}")

        expected = [("GATE-A", "approved"), ("GATE-B", "rejected")]
        actual = gate_statuses(db)
        if actual != expected:
            raise AssertionError(f"expected {expected!r}, got {actual!r}")

        print("PASS: multi-gate approve-then-reject statuses are stable")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
