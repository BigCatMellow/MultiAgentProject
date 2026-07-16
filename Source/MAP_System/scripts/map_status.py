#!/usr/bin/env python3
"""Print live MAP task-board status from SQLite."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "map.db"


def rows(conn: sqlite3.Connection, sql: str) -> list[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    return list(conn.execute(sql))


def print_table(title: str, headers: list[str], data: Iterable[sqlite3.Row]) -> None:
    data = list(data)
    print(title)
    if not data:
        print("  none")
        print()
        return
    widths = [
        max(len(header), *(len(str(row[header] or "")) for row in data))
        for header in headers
    ]
    print("  " + "  ".join(header.ljust(width) for header, width in zip(headers, widths)))
    print("  " + "  ".join("-" * width for width in widths))
    for row in data:
        print("  " + "  ".join(str(row[header] or "").ljust(width) for header, width in zip(headers, widths)))
    print()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    args = parser.parse_args()

    with sqlite3.connect(args.db) as conn:
        print_table(
            "IN_PROGRESS claims",
            ["task_id", "title", "claimed_by", "lease_expires_at", "heartbeat_at", "attempt", "max_attempts"],
            rows(
                conn,
                """
                SELECT task_id, title, claimed_by, lease_expires_at, heartbeat_at, attempt, max_attempts
                FROM tasks
                WHERE status='IN_PROGRESS'
                ORDER BY lease_expires_at, task_id
                """,
            ),
        )
        print_table(
            "SUBMITTED awaiting review",
            ["task_id", "title", "owner", "updated_at"],
            rows(
                conn,
                """
                SELECT task_id, title, owner, updated_at
                FROM tasks
                WHERE status='SUBMITTED'
                ORDER BY updated_at, task_id
                """,
            ),
        )
        print_table(
            "Pending approval gates",
            ["gate_id", "name", "required_after_task", "created_at"],
            rows(
                conn,
                """
                SELECT gate_id, name, required_after_task, created_at
                FROM approval_gates
                WHERE status='pending'
                ORDER BY created_at, gate_id
                """,
            ),
        )
        print_table(
            "Agent statuses",
            ["agent_id", "status", "agent_type", "reason", "resume_after", "last_heartbeat"],
            rows(
                conn,
                """
                SELECT agent_id, status, agent_type, reason, resume_after, last_heartbeat
                FROM agents
                ORDER BY agent_type, agent_id
                """,
            ),
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
