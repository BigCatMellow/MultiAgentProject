#!/usr/bin/env python3
"""Tests for no-self-review claim gate."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.db.claims import claim_block_reason, claim_task, claim_task_with_reason  # noqa: E402


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript((ROOT / "migration" / "schema.sql").read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES ('codex-a', 'Codex A', 'core', 'available')"
        )
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES ('claude-b', 'Claude B', 'core', 'available')"
        )


def insert_review_task(path: Path, *, owner: str = "codex-a") -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status, owner, attempt, max_attempts)
            VALUES ('TASK-R', 'TEST', 'Review task', 'Review a submitted task.', 'review', 'reviewer', 'READY', ?, 0, 3)
            """,
            (owner,),
        )
        conn.execute(
            "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES ('TASK-R', 'review artifact exists')"
        )


def fetch_status(path: Path) -> tuple[str, str | None]:
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT status, claimed_by FROM tasks WHERE task_id='TASK-R'").fetchone()
    assert row is not None
    return row[0], row[1]


def test_same_agent_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        init_db(db)
        insert_review_task(db, owner="codex-a")

        assert claim_block_reason("TASK-R", "codex-a", db_path=db) == "self_review"
        claimed, reason = claim_task_with_reason("TASK-R", "codex-a", db_path=db)

        assert not claimed
        assert reason == "self_review"
        assert not claim_task("TASK-R", "codex-a", db_path=db)
        assert fetch_status(db) == ("READY", None)


def test_different_agent_allowed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "test.db"
        init_db(db)
        insert_review_task(db, owner="codex-a")

        claimed, reason = claim_task_with_reason("TASK-R", "claude-b", db_path=db)

        assert claimed
        assert reason is None
        assert fetch_status(db) == ("IN_PROGRESS", "claude-b")


def main() -> int:
    tests = [test_same_agent_blocked, test_different_agent_allowed]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
