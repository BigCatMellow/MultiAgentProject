#!/usr/bin/env python3
"""Regression tests for HPOM-004 review gate enforcement in map_task.py."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
MAP_TASK = ROOT / "scripts" / "map_task.py"
SCHEMA = ROOT / "migration" / "schema.sql"
EXPORTER = ROOT / "migration" / "export_to_files.py"

GOOD_REVIEW = """\
# Review Record: TASK-T

## Header

```
task_id:      TASK-T
reviewer:     claude-mako
review_date:  2026-06-29
task_owner:   codex-live
```

## Verdict

```
APPROVED
```

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | gate works | PASS | verified manually |

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| no scope creep | NOT BROKEN |

## Files Reviewed

- `MAP_System/scripts/map_task.py`
"""

SELF_REVIEW = GOOD_REVIEW.replace("reviewer:     claude-mako", "reviewer:     codex-live")


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES "
            "('codex-live', 'Codex Live', 'core', 'available')"
        )
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES "
            "('claude-mako', 'Claude Mako', 'core', 'available')"
        )
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role,
               status, owner, attempt, max_attempts)
            VALUES
              ('TASK-T', 'TEST', 'Test task', 'desc', 'implementation',
               'implementer', 'SUBMITTED', 'codex-live', 0, 3)
            """
        )
        conn.execute(
            "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES "
            "('TASK-T', 'gate works')"
        )


def run_approve(db: Path, out: Path, review_record: Path | None) -> subprocess.CompletedProcess:
    event_log = out / "events" / "events.jsonl"
    cmd = [
        sys.executable, str(MAP_TASK),
        "--db", str(db),
        "--output-dir", str(out),
        "--event-log", str(event_log),
        "approve", "TASK-T",
        "--reviewer", "claude-mako",
    ]
    if review_record is not None:
        cmd += ["--review-record", str(review_record)]
    return subprocess.run(cmd, cwd=REPO, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def export_mirrors(db: Path, out: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(EXPORTER), "--db", str(db), "--output-dir", str(out)],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stderr


def test_approve_without_review_record_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)

        result = run_approve(db, out, review_record=None)
        assert result.returncode != 0, (
            f"expected non-zero exit when no --review-record provided, got 0\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )
        assert "review-record" in result.stderr.lower() or "hpom" in result.stderr.lower(), (
            f"expected HPOM-004 error in stderr, got: {result.stderr!r}"
        )

        with sqlite3.connect(db) as conn:
            row = conn.execute("SELECT status FROM tasks WHERE task_id='TASK-T'").fetchone()
        assert row[0] == "SUBMITTED", f"task should remain SUBMITTED, got {row[0]!r}"


def test_approve_with_invalid_review_record_fails() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)

        bad_review = base / "bad-review.md"
        bad_review.write_text(SELF_REVIEW, encoding="utf-8")

        result = run_approve(db, out, review_record=bad_review)
        assert result.returncode != 0, (
            f"expected non-zero exit for self-review record, got 0\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

        with sqlite3.connect(db) as conn:
            row = conn.execute("SELECT status FROM tasks WHERE task_id='TASK-T'").fetchone()
        assert row[0] == "SUBMITTED", f"task should remain SUBMITTED, got {row[0]!r}"


def test_approve_with_valid_review_record_succeeds() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)

        good_review = base / "good-review.md"
        good_review.write_text(GOOD_REVIEW, encoding="utf-8")
        export_mirrors(db, out)

        result = run_approve(db, out, review_record=good_review)
        assert result.returncode == 0, (
            f"expected zero exit for valid review record, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

        with sqlite3.connect(db) as conn:
            row = conn.execute("SELECT status FROM tasks WHERE task_id='TASK-T'").fetchone()
        assert row[0] == "APPROVED", f"task should be APPROVED, got {row[0]!r}"


def main() -> int:
    tests = [
        test_approve_without_review_record_fails,
        test_approve_with_invalid_review_record_fails,
        test_approve_with_valid_review_record_succeeds,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
