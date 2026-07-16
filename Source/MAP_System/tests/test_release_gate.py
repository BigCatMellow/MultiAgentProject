#!/usr/bin/env python3
"""Regression tests for HPOM-006 release gate enforcement."""

from __future__ import annotations

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCHEMA = ROOT / "migration" / "schema.sql"
RELEASE_TASK = ROOT / "scripts" / "release_task.py"
MAP_TASK = ROOT / "scripts" / "map_task.py"
EXPORTER = ROOT / "migration" / "export_to_files.py"

VALID_CHECKLIST = """\
# Release Checklist: TASK-R

## Header

```
task_id:      TASK-R
released_by:  codex-live
release_date: 2026-06-29
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

Ready to release.
"""

INCOMPLETE_CHECKLIST = VALID_CHECKLIST.replace(
    "- [x] Follow-up tasks created",
    "- [ ] Follow-up tasks created",
)

MISSING_EMERGENCE_CHECKLIST = VALID_CHECKLIST.replace(
    "- [x] Emergence capture considered\n", ""
)


def init_db(path: Path, *, status: str = "APPROVED") -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES "
            "('codex-live', 'Codex Live', 'core', 'available')"
        )
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role,
               status, owner, attempt, max_attempts)
            VALUES
              ('TASK-R', 'TEST', 'Release task', 'desc', 'implementation',
               'implementer', ?, 'codex-live', 0, 3)
            """,
            (status,),
        )


def run_release_task(db: Path, out: Path, checklist: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, str(RELEASE_TASK),
            "TASK-R",
            "--released-by", "codex-live",
            "--checklist", str(checklist),
            "--db", str(db),
            "--output-dir", str(out),
            "--event-log", str(out / "events" / "events.jsonl"),
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def run_map_task_release(db: Path, out: Path, checklist: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable, str(MAP_TASK),
            "--db", str(db),
            "--output-dir", str(out),
            "--event-log", str(out / "events" / "events.jsonl"),
            "release", "TASK-R",
            "--released-by", "codex-live",
            "--checklist", str(checklist),
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def export_mirrors(db: Path, out: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(EXPORTER), "--db", str(db), "--output-dir", str(out)],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert result.returncode == 0, result.stderr


def task_state(path: Path) -> tuple[str, int]:
    with sqlite3.connect(path) as conn:
        status = conn.execute("SELECT status FROM tasks WHERE task_id='TASK-R'").fetchone()[0]
        count = conn.execute("SELECT count(*) FROM task_release_records WHERE task_id='TASK-R'").fetchone()[0]
    return status, count


def test_incomplete_checklist_blocks_release() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        checklist = base / "release.md"
        init_db(db)
        checklist.write_text(INCOMPLETE_CHECKLIST, encoding="utf-8")

        result = run_release_task(db, out, checklist)

        assert result.returncode != 0, result.stdout
        assert "incomplete" in result.stderr.lower(), result.stderr
        assert task_state(db) == ("APPROVED", 0)


def test_missing_emergence_line_blocks_release() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        checklist = base / "release.md"
        init_db(db)
        checklist.write_text(MISSING_EMERGENCE_CHECKLIST, encoding="utf-8")

        result = run_release_task(db, out, checklist)

        assert result.returncode != 0, result.stdout
        assert "emergence capture considered" in result.stderr.lower(), result.stderr
        assert task_state(db) == ("APPROVED", 0)


def test_release_task_marks_released_with_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        checklist = base / "release.md"
        init_db(db)
        checklist.write_text(VALID_CHECKLIST, encoding="utf-8")
        export_mirrors(db, out)

        result = run_release_task(db, out, checklist)

        assert result.returncode == 0, result.stderr
        assert task_state(db) == ("RELEASED", 1)


def test_map_task_release_subcommand() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        checklist = base / "release.md"
        init_db(db)
        checklist.write_text(VALID_CHECKLIST, encoding="utf-8")
        export_mirrors(db, out)

        result = run_map_task_release(db, out, checklist)

        assert result.returncode == 0, result.stderr
        assert task_state(db) == ("RELEASED", 1)


def main() -> int:
    tests = [
        test_incomplete_checklist_blocks_release,
        test_missing_emergence_line_blocks_release,
        test_release_task_marks_released_with_record,
        test_map_task_release_subcommand,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
