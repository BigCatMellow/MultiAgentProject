#!/usr/bin/env python3
"""Create a conflict record and move the affected task to CONFLICT status.

HPOM-008: When an agent finds a contradiction, it must stop, create a conflict
record, and move the affected task to CONFLICT. The task cannot resume without
a resolution record.

Usage:
    python3 MAP_System/scripts/flag_conflict.py \\
        --task-id TASK-NNN \\
        --type AUTHORITY_CONFLICT \\
        --source-a "shared/decisions.md DEC-001" \\
        --source-b "shared/decisions.md DEC-007" \\
        --summary "DEC-001 says X but DEC-007 says Y" \\
        --decision-owner command-center \\
        --raised-by [agent-id]

Exit codes:
    0  conflict record created, task moved to CONFLICT
    1  error (task not found, already in terminal state, etc.)
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "map.db"
CONFLICTS_DIR = ROOT / "artifacts" / "conflicts"
EVENT_LOG = ROOT / "events" / "events.jsonl"

CONFLICT_TYPES = [
    "AUTHORITY_CONFLICT",
    "SCOPE_CONFLICT",
    "STATE_CONFLICT",
    "DECISION_CONFLICT",
    "FACTUAL_CONFLICT",
]

TERMINAL_STATUSES = {"DONE", "APPROVED", "RELEASED", "CANCELLED"}


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def next_conflict_id(conflicts_dir: Path) -> str:
    existing = sorted(conflicts_dir.glob("CONFLICT-*.md"))
    if not existing:
        return "CONFLICT-001"
    last = existing[-1].stem  # e.g. CONFLICT-007
    num = int(last.split("-")[1]) + 1
    return f"CONFLICT-{num:03d}"


def create_conflict_record(
    conflict_id: str,
    task_id: str,
    conflict_type: str,
    source_a: str,
    source_b: str,
    summary: str,
    decision_owner: str,
    raised_by: str,
    raised_at: str,
) -> Path:
    CONFLICTS_DIR.mkdir(parents=True, exist_ok=True)
    out = CONFLICTS_DIR / f"{conflict_id}.md"

    content = f"""# Conflict Record: {conflict_id}

## Header

```
conflict_id:    {conflict_id}
raised_by:      {raised_by}
raised_at:      {raised_at}
affected_task:  {task_id}
status:         OPEN
decision_owner: {decision_owner}
```

## Conflict Type

```
{conflict_type}
```

## Conflicting Sources

| Source A | Source B |
|---|---|
| {source_a} | {source_b} |

## Summary

{summary}

## Affected Files

- (fill in files affected by or containing the conflict)

## Impact

Task {task_id} is blocked. Work cannot resume without a resolution record.

## Resolution

```
status:       OPEN
resolved_by:  (pending)
resolved_at:  (pending)
decision_ref: (pending)
```

Resolution statement: (pending — decision owner: {decision_owner})

## Follow-up Tasks

- [ ] (created after resolution)
"""
    out.write_text(content, encoding="utf-8")
    return out


def move_task_to_conflict(task_id: str, conflict_id: str, db_path: Path) -> bool:
    """Move task to CONFLICT status in SQLite. Returns True if updated."""
    with connect(db_path) as conn:
        row = conn.execute(
            "SELECT status FROM tasks WHERE task_id = ?", (task_id,)
        ).fetchone()
        if row is None:
            print(f"ERROR: task not found: {task_id}", file=sys.stderr)
            return False
        current = row["status"]
        if current in TERMINAL_STATUSES:
            print(
                f"ERROR: task {task_id} is in terminal status {current}; cannot move to CONFLICT",
                file=sys.stderr,
            )
            return False

        # CONFLICT may not exist in older schemas — add it gracefully
        try:
            conn.execute(
                """
                UPDATE tasks
                SET status = 'CONFLICT', updated_at = datetime('now')
                WHERE task_id = ?
                """,
                (task_id,),
            )
        except sqlite3.OperationalError as exc:
            print(f"ERROR updating task: {exc}", file=sys.stderr)
            return False
    return True


def log_event(task_id: str, conflict_id: str, raised_by: str, record_path: Path) -> None:
    entry = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "type": "CONFLICT",
        "task_id": task_id,
        "agent": raised_by,
        "summary": f"Conflict flagged: {conflict_id}. Task moved to CONFLICT status.",
        "artifact_paths": [str(record_path.relative_to(ROOT.parent))],
    }
    with EVENT_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument(
        "--type",
        required=True,
        choices=CONFLICT_TYPES,
        dest="conflict_type",
        help="Conflict classification",
    )
    parser.add_argument("--source-a", required=True, help="First conflicting source")
    parser.add_argument("--source-b", required=True, help="Second conflicting source")
    parser.add_argument("--summary", required=True, help="Plain-text description of the contradiction")
    parser.add_argument("--decision-owner", required=True, help="Who can resolve this conflict")
    parser.add_argument("--raised-by", required=True, help="Agent ID raising the conflict")
    parser.add_argument("--db", default=str(DEFAULT_DB))
    args = parser.parse_args(argv)

    db_path = Path(args.db)
    raised_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    conflict_id = next_conflict_id(CONFLICTS_DIR)

    record_path = create_conflict_record(
        conflict_id=conflict_id,
        task_id=args.task_id,
        conflict_type=args.conflict_type,
        source_a=args.source_a,
        source_b=args.source_b,
        summary=args.summary,
        decision_owner=args.decision_owner,
        raised_by=args.raised_by,
        raised_at=raised_at,
    )
    print(f"Conflict record created: {record_path}")

    if not move_task_to_conflict(args.task_id, conflict_id, db_path):
        return 1

    print(f"Task {args.task_id} moved to CONFLICT status.")
    log_event(args.task_id, conflict_id, args.raised_by, record_path)
    print(f"Event logged. Conflict ID: {conflict_id}")
    print(f"\nNext step: {args.decision_owner} must resolve {conflict_id} before {args.task_id} can resume.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
