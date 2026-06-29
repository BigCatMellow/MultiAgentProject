#!/usr/bin/env python3
"""Print read-only MAP health metrics from SQLite and shared-state files."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "map.db"
DEFAULT_SHARED = ROOT / "shared"
VALIDATE_SHARED = ROOT / "scripts" / "validate_shared_state.py"


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def task_counts(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute(
        """
        SELECT status, count(*) AS count
        FROM tasks
        GROUP BY status
        ORDER BY status
        """
    ).fetchall()
    return {row["status"]: row["count"] for row in rows}


def scalar(conn: sqlite3.Connection, sql: str) -> int:
    row = conn.execute(sql).fetchone()
    return int(row[0]) if row else 0


def stale_shared_count(shared_dir: Path) -> int:
    if not VALIDATE_SHARED.exists() or not shared_dir.exists():
        return 0
    result = subprocess.run(
        [sys.executable, str(VALIDATE_SHARED), "--shared-dir", str(shared_dir), "--strict"],
        cwd=ROOT.parent,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    count = 0
    for line in result.stdout.splitlines():
        if "STATUS_STALE" in line or "STATUS_SUPERSEDED" in line or "STATUS_NEEDS_REVIEW" in line:
            count += 1
    return count


def event_counts(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute(
        """
        SELECT event_type, count(*) AS count
        FROM events
        GROUP BY event_type
        ORDER BY event_type
        """
    ).fetchall()
    return {row["event_type"]: row["count"] for row in rows}


def collect_metrics(db_path: Path, shared_dir: Path) -> dict[str, Any]:
    with connect(db_path) as conn:
        counts = task_counts(conn)
        submitted = counts.get("SUBMITTED", 0)
        conflicts = counts.get("CONFLICT", 0)
        events = event_counts(conn)
    approvals = events.get("APPROVED", 0)
    changes = events.get("CHANGES_REQUESTED", 0)
    reviewed = approvals + changes
    change_request_rate = (changes / reviewed) if reviewed else 0.0
    return {
        "task_counts": counts,
        "review_queue_size": submitted,
        "conflict_count": conflicts,
        "stale_shared_file_count": stale_shared_count(shared_dir),
        "change_request_rate": change_request_rate,
        "event_counts": events,
    }


def print_table(metrics: dict[str, Any]) -> None:
    print("MAP Health Metrics")
    print()
    print("Task counts by status")
    print("| Status | Count |")
    print("|---|---:|")
    for status, count in metrics["task_counts"].items():
        print(f"| {status} | {count} |")
    print()
    print("Queue and health")
    print("| Metric | Value |")
    print("|---|---:|")
    print(f"| Review queue size | {metrics['review_queue_size']} |")
    print(f"| Conflict count | {metrics['conflict_count']} |")
    print(f"| Stale shared file count | {metrics['stale_shared_file_count']} |")
    print(f"| Change request rate | {metrics['change_request_rate']:.2%} |")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--shared-dir", type=Path, default=DEFAULT_SHARED)
    parser.add_argument("--json", action="store_true", help="Emit metrics as JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        metrics = collect_metrics(args.db, args.shared_dir)
    except sqlite3.Error as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(metrics, indent=2, sort_keys=True))
    else:
        print_table(metrics)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
