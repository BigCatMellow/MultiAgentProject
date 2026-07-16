#!/usr/bin/env python3
"""Expire stale SQLite task leases once and log the result."""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from db.claims import DEFAULT_DB, expire_leases  # noqa: E402


EVENT_LOG = ROOT / "events" / "events.jsonl"


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def event_payload(expired_task_ids: list[str]) -> dict[str, object]:
    count = len(expired_task_ids)
    task_list = ", ".join(expired_task_ids) if expired_task_ids else "none"
    return {
        "created_at": now(),
        "type": "PROGRESS",
        "task_id": None,
        "sender": "reconcile",
        "summary": f"Expired stale task leases: count={count}; task_ids={task_list}.",
        "artifact_paths": ["MAP_System/map.db"],
    }


def append_jsonl(payload: dict[str, object]) -> None:
    EVENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    with EVENT_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")


def append_sqlite(payload: dict[str, object], db_path: Path = DEFAULT_DB) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            INSERT INTO agents (agent_id, label, agent_type, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET
                label = excluded.label,
                agent_type = excluded.agent_type,
                status = excluded.status,
                updated_at = datetime('now')
            """,
            ("reconcile", "Reconcile", "system", "available"),
        )
        conn.execute(
            """
            INSERT INTO events
                (event_type, task_id, sender_id, summary, artifact_paths, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload["type"],
                payload["task_id"],
                payload["sender"],
                payload["summary"],
                json.dumps(payload["artifact_paths"], sort_keys=True),
                payload["created_at"],
            ),
        )


def main() -> int:
    expired_task_ids = list(expire_leases(db_path=DEFAULT_DB))
    payload = event_payload(expired_task_ids)
    append_jsonl(payload)
    append_sqlite(payload)
    print(f"expired_count={len(expired_task_ids)}")
    print("expired_task_ids=" + (",".join(expired_task_ids) if expired_task_ids else "none"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
