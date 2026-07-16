#!/usr/bin/env python3
"""Tests for atomic review claiming (TASK-199 / IDEA-0017)."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "migration" / "schema.sql"

if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from MAP_System.db.claims import claim_review, get_open_review_claim, release_review_claim


def init_db(path: Path, *, status: str = "SUBMITTED", owner: str = "owner-agent") -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES "
            "(?, 'Owner', 'core', 'available')",
            (owner,),
        )
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES "
            "('reviewer-a', 'Reviewer A', 'core', 'available'), "
            "('reviewer-b', 'Reviewer B', 'core', 'available')"
        )
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status,
               owner, attempt, max_attempts)
            VALUES
              ('TASK-R', 'TEST', 'Reviewable task', 'desc', 'implementation',
               'worker', ?, ?, 0, 3)
            """,
            (status, owner),
        )


def test_claim_review_succeeds_on_submitted_task():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db)
        assert claim_review("TASK-R", "reviewer-a", db_path=db) is True
        claim = get_open_review_claim("TASK-R", db_path=db)
        assert claim is not None
        assert claim["reviewer_id"] == "reviewer-a"


def test_concurrent_claim_race_only_one_wins():
    """The core guarantee: two reviewers racing for the same SUBMITTED task
    can never both hold an open claim -- the unique index arbitrates."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db)
        first = claim_review("TASK-R", "reviewer-a", db_path=db)
        second = claim_review("TASK-R", "reviewer-b", db_path=db)
        assert first is True
        assert second is False
        claim = get_open_review_claim("TASK-R", db_path=db)
        assert claim["reviewer_id"] == "reviewer-a"


def test_self_review_blocked():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db, owner="owner-agent")
        assert claim_review("TASK-R", "owner-agent", db_path=db) is False
        assert get_open_review_claim("TASK-R", db_path=db) is None


def test_claim_requires_submitted_status():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db, status="IN_PROGRESS")
        assert claim_review("TASK-R", "reviewer-a", db_path=db) is False


def test_claim_unknown_task_returns_false():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db)
        assert claim_review("TASK-GHOST", "reviewer-a", db_path=db) is False


def test_release_by_holder_succeeds_and_frees_the_slot():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db)
        assert claim_review("TASK-R", "reviewer-a", db_path=db) is True
        assert release_review_claim(
            "TASK-R", "reviewer-a", verdict="APPROVED", summary="looks good",
            db_path=db,
        ) is True
        assert get_open_review_claim("TASK-R", db_path=db) is None
        # slot is free again: a new reviewer can claim
        assert claim_review("TASK-R", "reviewer-b", db_path=db) is True


def test_release_by_non_holder_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db)
        assert claim_review("TASK-R", "reviewer-a", db_path=db) is True
        assert release_review_claim("TASK-R", "reviewer-b", db_path=db) is False
        # original claim is untouched
        claim = get_open_review_claim("TASK-R", db_path=db)
        assert claim["reviewer_id"] == "reviewer-a"


def test_release_with_no_open_claim_returns_false():
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db)
        assert release_review_claim("TASK-R", "reviewer-a", db_path=db) is False


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} review-claim tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
