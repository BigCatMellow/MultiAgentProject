#!/usr/bin/env python3
"""Release APPROVED MAP tasks after a completed HPOM checklist."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

try:
    from MAP_System.scripts.event_trace import add_trace_fields
except ModuleNotFoundError:  # direct script execution
    from event_trace import add_trace_fields


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "map.db"
EXPORTER = ROOT / "migration" / "export_to_files.py"
EVENT_LOG = ROOT / "events" / "events.jsonl"
VALIDATE_TASK_MIRRORS = ROOT / "scripts" / "validate_task_mirrors.py"

REQUIRED_CHECKS = {
    "shared-file updates": re.compile(r"^\s*-\s*\[[xX]\]\s*Shared-file updates complete\s*$", re.MULTILINE),
    "decisions recorded": re.compile(r"^\s*-\s*\[[xX]\]\s*Decisions recorded\s*$", re.MULTILINE),
    "follow-up tasks created": re.compile(r"^\s*-\s*\[[xX]\]\s*Follow-up tasks created\s*$", re.MULTILINE),
    "event log entry": re.compile(r"^\s*-\s*\[[xX]\]\s*Event log entry prepared\s*$", re.MULTILINE),
    "emergence capture considered": re.compile(r"^\s*-\s*\[[xX]\]\s*Emergence capture considered\s*$", re.MULTILINE),
}

TASK_ID_RE = re.compile(r"task_id\s*:\s*(TASK-\w+)", re.IGNORECASE)


class ReleaseError(RuntimeError):
    pass


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS task_release_records (
            task_id         TEXT PRIMARY KEY REFERENCES tasks(task_id),
            checklist_path  TEXT NOT NULL,
            released_by     TEXT NOT NULL REFERENCES agents(agent_id),
            summary         TEXT NOT NULL DEFAULT '',
            created_at      TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
        )
        """
    )


def ensure_agent(conn: sqlite3.Connection, agent_id: str) -> None:
    conn.execute(
        """
        INSERT OR IGNORE INTO agents (agent_id, label, agent_type, status)
        VALUES (?, ?, 'core', 'available')
        """,
        (agent_id, agent_id.replace("-", " ").title()),
    )


def validate_checklist(path: Path, task_id: str) -> str:
    if not path.exists():
        raise ReleaseError(f"release checklist not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    match = TASK_ID_RE.search(text[:500])
    if not match:
        raise ReleaseError("release checklist is missing task_id header")
    found_id = match.group(1).strip()
    if found_id.upper() != task_id.upper():
        raise ReleaseError(f"release checklist task_id is {found_id}, expected {task_id}")
    missing = [name for name, pattern in REQUIRED_CHECKS.items() if not pattern.search(text)]
    if missing:
        raise ReleaseError("release checklist incomplete: " + ", ".join(missing))
    return text


def append_event(
    db_path: Path,
    event_log: Path,
    task_id: str,
    released_by: str,
    checklist_path: Path,
) -> None:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    summary = f"{task_id} released by {released_by} with checklist {checklist_path}."
    paths = [str(checklist_path), f"MAP_System/tasks/{task_id}.json", "MAP_System/workflow/task_graph.json"]
    payload = {
        "created_at": created_at,
        "type": "RELEASED",
        "task_id": task_id,
        "sender": released_by,
        "summary": summary,
        "artifact_paths": paths,
    }
    add_trace_fields(payload, actor=released_by, action="release", target=task_id)
    event_log.parent.mkdir(parents=True, exist_ok=True)
    with event_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")
    with connect(db_path) as conn:
        ensure_schema(conn)
        ensure_agent(conn, released_by)
        conn.execute(
            """
            INSERT OR IGNORE INTO events
                (event_type, task_id, sender_id, summary, artifact_paths, created_at)
            VALUES ('RELEASED', ?, ?, ?, ?, ?)
            """,
            (task_id, released_by, summary, json.dumps(paths), created_at),
        )


def sync_files(db_path: Path, output_dir: Path | None) -> None:
    cmd = [sys.executable, str(EXPORTER), "--db", str(db_path)]
    if output_dir:
        cmd.extend(["--output-dir", str(output_dir)])
    subprocess.run(cmd, cwd=ROOT.parent, check=True)


def validate_task_mirrors(db_path: Path, output_dir: Path | None) -> None:
    root = output_dir if output_dir else ROOT
    subprocess.run(
        [sys.executable, str(VALIDATE_TASK_MIRRORS), "--db", str(db_path), "--root", str(root)],
        cwd=ROOT.parent,
        check=True,
    )


def release_task(
    task_id: str,
    released_by: str,
    checklist: Path,
    *,
    db_path: Path = DEFAULT_DB,
    event_log: Path = EVENT_LOG,
    output_dir: Path | None = None,
    summary: str = "",
) -> None:
    validate_checklist(checklist, task_id)
    validate_task_mirrors(db_path, output_dir)
    with connect(db_path) as conn:
        ensure_schema(conn)
        task = conn.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if task is None:
            raise ReleaseError(f"unknown task: {task_id}")
        if task["status"] != "APPROVED":
            raise ReleaseError(f"{task_id} is {task['status']}, not APPROVED")
        ensure_agent(conn, released_by)
        conn.execute(
            """
            INSERT INTO task_release_records (task_id, checklist_path, released_by, summary)
            VALUES (?, ?, ?, ?)
            """,
            (task_id, str(checklist), released_by, summary),
        )
        conn.execute(
            """
            UPDATE tasks
            SET status = 'RELEASED',
                claimed_by = NULL,
                lease_expires_at = NULL,
                heartbeat_at = NULL,
                updated_at = datetime('now')
            WHERE task_id = ?
            """,
            (task_id,),
        )
    append_event(db_path, event_log, task_id, released_by, checklist)
    sync_files(db_path, output_dir)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("task_id")
    parser.add_argument("--released-by", required=True)
    parser.add_argument("--checklist", type=Path, required=True)
    parser.add_argument("--summary", default="")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--event-log", type=Path, default=EVENT_LOG)
    parser.add_argument("--output-dir", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        release_task(
            args.task_id,
            args.released_by,
            args.checklist,
            db_path=args.db,
            event_log=args.event_log,
            output_dir=args.output_dir,
            summary=args.summary,
        )
    except (ReleaseError, sqlite3.Error, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({"task_id": args.task_id, "status": "RELEASED"}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
