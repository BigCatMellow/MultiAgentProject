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

EVENT_ALIASES = {
    "REVIEW_APPROVED": "APPROVED",
    "REVIEW_CHANGES_REQUESTED": "CHANGES_REQUESTED",
    "task_progress": "PROGRESS",
}
OUTCOME_EVENT_TYPES = {"outcome_pass", "outcome_fail"}
OUTCOME_KNOWN_STATUSES = {"pass", "fail", "partial"}


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
    counts: dict[str, int] = {}
    for row in rows:
        event_type = EVENT_ALIASES.get(row["event_type"], row["event_type"])
        counts[event_type] = counts.get(event_type, 0) + row["count"]
    return counts


def summary_payload(summary: str) -> dict[str, Any]:
    try:
        parsed = json.loads(summary)
    except (TypeError, json.JSONDecodeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def outcome_feedback_metrics(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT event_type, summary
        FROM events
        WHERE lower(event_type) IN ('outcome_pass', 'outcome_fail')
        ORDER BY created_at, id
        """
    ).fetchall()
    total = 0
    known_with_passed_validation = 0
    blind_spots = 0
    for row in rows:
        event_type = row["event_type"].lower()
        payload = summary_payload(row["summary"])
        outcome_status = str(payload.get("outcome_status") or event_type.removeprefix("outcome_")).lower()
        validation_status = str(payload.get("validation_status_at_ship") or "").lower()
        if event_type in OUTCOME_EVENT_TYPES:
            total += 1
        if outcome_status not in OUTCOME_KNOWN_STATUSES:
            continue
        if validation_status != "passed":
            continue
        known_with_passed_validation += 1
        if event_type == "outcome_fail":
            blind_spots += 1
    rate = (
        blind_spots / known_with_passed_validation
        if known_with_passed_validation
        else 0.0
    )
    return {
        "outcome_event_count": total,
        "validator_blind_spot_count": blind_spots,
        "validator_blind_spot_denominator": known_with_passed_validation,
        "validator_blind_spot_rate": rate,
    }


def collect_metrics(db_path: Path, shared_dir: Path) -> dict[str, Any]:
    with connect(db_path) as conn:
        counts = task_counts(conn)
        submitted = counts.get("SUBMITTED", 0)
        conflicts = counts.get("CONFLICT", 0)
        events = event_counts(conn)
        outcome_feedback = outcome_feedback_metrics(conn)
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
        "outcome_feedback": outcome_feedback,
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
    print(
        "| Validator blind-spot rate | "
        f"{metrics['outcome_feedback']['validator_blind_spot_rate']:.2%} |"
    )
    print(
        "| Validator blind-spot count | "
        f"{metrics['outcome_feedback']['validator_blind_spot_count']} / "
        f"{metrics['outcome_feedback']['validator_blind_spot_denominator']} |"
    )


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
