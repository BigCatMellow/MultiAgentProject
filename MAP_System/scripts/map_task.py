#!/usr/bin/env python3
"""Manage MAP tasks in SQLite and sync file mirrors."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

VALIDATE_REVIEW = Path(__file__).resolve().parent / "validate_review.py"
RELEASE_TASK = Path(__file__).resolve().parent / "release_task.py"


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "map.db"
EXPORTER = ROOT / "migration" / "export_to_files.py"
EVENT_LOG = ROOT / "events" / "events.jsonl"


class UsageError(RuntimeError):
    pass


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def project_id(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT project_id FROM tasks ORDER BY task_id LIMIT 1").fetchone()
    return row["project_id"] if row else "MAP-BOOTSTRAP-20260617"


def ensure_agent(conn: sqlite3.Connection, agent_id: str | None) -> None:
    if not agent_id:
        return
    conn.execute(
        """
        INSERT OR IGNORE INTO agents (agent_id, label, agent_type, status)
        VALUES (?, ?, 'core', 'available')
        """,
        (agent_id, agent_id.replace("-", " ").title()),
    )


def task_payload(conn: sqlite3.Connection, task_id: str) -> dict[str, Any]:
    task = conn.execute(
        """
        SELECT task_id, project_id, title, description, task_type, role, status,
               priority, required_agent, owner, claimed_by, lease_expires_at,
               heartbeat_at, attempt, max_attempts, created_at, updated_at
        FROM tasks
        WHERE task_id=?
        """,
        (task_id,),
    ).fetchone()
    if task is None:
        raise UsageError(f"unknown task: {task_id}")
    payload = dict(task)
    payload["dependencies"] = [
        row["depends_on"]
        for row in conn.execute(
            "SELECT depends_on FROM task_dependencies WHERE task_id=? ORDER BY depends_on",
            (task_id,),
        )
    ]
    payload["output_paths"] = [
        row["path"]
        for row in conn.execute(
            "SELECT path FROM task_output_paths WHERE task_id=? ORDER BY path",
            (task_id,),
        )
    ]
    payload["acceptance_criteria"] = [
        row["criterion"]
        for row in conn.execute(
            "SELECT criterion FROM task_acceptance_criteria WHERE task_id=? ORDER BY id",
            (task_id,),
        )
    ]
    return payload


def append_event(
    db_path: Path,
    event_log: Path,
    event_type: str,
    task_id: str,
    sender: str,
    summary: str,
    paths: list[str],
) -> None:
    created_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    payload = {
        "created_at": created_at,
        "type": event_type,
        "task_id": task_id,
        "sender": sender,
        "summary": summary,
        "artifact_paths": paths,
    }
    event_log.parent.mkdir(parents=True, exist_ok=True)
    with event_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")
    with connect(db_path) as conn:
        ensure_agent(conn, sender)
        conn.execute(
            """
            INSERT OR IGNORE INTO events
                (event_type, task_id, sender_id, summary, artifact_paths, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_type, task_id, sender, summary, json.dumps(paths), created_at),
        )


def sync_files(db_path: Path, output_dir: Path | None) -> None:
    cmd = [sys.executable, str(EXPORTER), "--db", str(db_path)]
    if output_dir:
        cmd.extend(["--output-dir", str(output_dir)])
    subprocess.run(cmd, cwd=ROOT.parent, check=True)


def is_review_shape(task_type: str, role: str) -> bool:
    return task_type.lower() == "review" or role.lower() == "reviewer"


def next_task_id(conn: sqlite3.Connection) -> str:
    rows = conn.execute("SELECT task_id FROM tasks WHERE task_id GLOB 'TASK-[0-9]*'").fetchall()
    highest = 0
    for row in rows:
        suffix = str(row["task_id"]).split("-", 1)[-1]
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return f"TASK-{highest + 1:03d}"


def create_task(args: argparse.Namespace) -> int:
    initial_status = (
        "READY"
        if args.description.strip() and args.output_path and args.criterion
        else "NEEDS_SHAPING"
    )
    with connect(args.db) as conn:
        # Reserve auto IDs under an immediate write lock so concurrent agents do
        # not both read the same highest TASK-NNN before either inserts.
        conn.execute("BEGIN IMMEDIATE")
        task_id = next_task_id(conn) if args.task_id.lower() == "auto" else args.task_id
        if is_review_shape(args.task_type, args.role) and args.owner.lower() == args.actor.lower():
            print(
                f"warning: {task_id} is review-shaped and owner matches actor; "
                "the claim gate will block self-review claims",
                file=sys.stderr,
            )
        if conn.execute("SELECT 1 FROM tasks WHERE task_id=?", (task_id,)).fetchone():
            raise UsageError(f"task already exists: {task_id}")
        ensure_agent(conn, args.owner)
        ensure_agent(conn, args.required_agent)
        conn.execute(
            """
            INSERT INTO tasks
                (task_id, project_id, title, description, task_type, role, status,
                 priority, required_agent, owner, attempt, max_attempts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                task_id,
                project_id(conn),
                args.title,
                args.description or "",
                args.task_type,
                args.role,
                initial_status,
                args.priority,
                args.required_agent,
                args.owner,
                args.max_attempts,
            ),
        )
        for dep in args.depends_on:
            if not conn.execute("SELECT 1 FROM tasks WHERE task_id=?", (dep,)).fetchone():
                raise UsageError(f"unknown dependency: {dep}")
            conn.execute(
                "INSERT INTO task_dependencies (task_id, depends_on) VALUES (?, ?)",
                (task_id, dep),
            )
        for path in args.output_path:
            conn.execute(
                "INSERT INTO task_output_paths (task_id, path) VALUES (?, ?)",
                (task_id, path),
            )
        for criterion in args.criterion:
            conn.execute(
                "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES (?, ?)",
                (task_id, criterion),
            )
    paths = [f"MAP_System/tasks/{task_id}.json", "MAP_System/workflow/task_graph.json"]
    append_event(args.db, args.event_log, "PROGRESS", task_id, args.actor, f"Created {task_id}: {args.title} ({initial_status})", paths)
    sync_files(args.db, args.output_dir)
    print(json.dumps({"created": task_id}, separators=(",", ":")))
    return 0


def set_review_state(args: argparse.Namespace, *, approved: bool) -> int:
    status = "APPROVED" if approved else "CHANGES_REQUESTED"
    event_type = "APPROVED" if approved else "CHANGES_REQUESTED"

    # HPOM-004: review record is mandatory for APPROVED status
    if approved:
        if not getattr(args, "review_record", None):
            raise UsageError(
                "--review-record is required for APPROVED status (HPOM-004); "
                "provide a review record file validated by validate_review.py"
            )
        result = subprocess.run(
            [sys.executable, str(VALIDATE_REVIEW),
             "--review-record", str(args.review_record),
             "--task-id", args.task_id],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stderr, file=sys.stderr, end="")
            raise UsageError(f"review record validation failed for {args.task_id}")

    with connect(args.db) as conn:
        task = conn.execute("SELECT status, title FROM tasks WHERE task_id=?", (args.task_id,)).fetchone()
        if task is None:
            raise UsageError(f"unknown task: {args.task_id}")
        if task["status"] != "SUBMITTED":
            raise UsageError(f"{args.task_id} is {task['status']}, not SUBMITTED")
        ensure_agent(conn, args.reviewer)
        conn.execute(
            """
            UPDATE tasks
            SET status=?, claimed_by=NULL, lease_expires_at=NULL, heartbeat_at=NULL,
                updated_at=datetime('now')
            WHERE task_id=?
            """,
            (status, args.task_id),
        )
    summary = (
        f"{args.task_id} approved by {args.reviewer}."
        if approved
        else f"{args.task_id} rejected by {args.reviewer}: {args.reason}"
    )
    append_event(
        args.db,
        args.event_log,
        event_type,
        args.task_id,
        args.reviewer,
        summary,
        [f"MAP_System/tasks/{args.task_id}.json", "MAP_System/workflow/task_graph.json"],
    )
    sync_files(args.db, args.output_dir)
    print(json.dumps({"task_id": args.task_id, "status": status}, separators=(",", ":")))
    return 0


def rework_task(args: argparse.Namespace) -> int:
    with connect(args.db) as conn:
        task = conn.execute("SELECT status, owner FROM tasks WHERE task_id=?", (args.task_id,)).fetchone()
        if task is None:
            raise UsageError(f"unknown task: {args.task_id}")
        if task["status"] != "CHANGES_REQUESTED":
            raise UsageError(f"{args.task_id} is {task['status']}, not CHANGES_REQUESTED")
        ensure_agent(conn, args.actor)
        conn.execute(
            """
            UPDATE tasks
            SET status='READY',
                claimed_by=NULL,
                lease_expires_at=NULL,
                heartbeat_at=NULL,
                updated_at=datetime('now')
            WHERE task_id=?
            """,
            (args.task_id,),
        )
    append_event(
        args.db,
        args.event_log,
        "PROGRESS",
        args.task_id,
        args.actor,
        f"{args.task_id} returned to READY for rework by {args.actor}: {args.reason}",
        [f"MAP_System/tasks/{args.task_id}.json", "MAP_System/workflow/task_graph.json"],
    )
    sync_files(args.db, args.output_dir)
    print(json.dumps({"task_id": args.task_id, "status": "READY"}, separators=(",", ":")))
    return 0


def show_task(args: argparse.Namespace) -> int:
    with connect(args.db) as conn:
        print(json.dumps(task_payload(conn, args.task_id), indent=2))
    return 0


def log_task(args: argparse.Namespace) -> int:
    """Print a readable timeline for a task: record + events + linked artifacts."""
    with connect(args.db) as conn:
        payload = task_payload(conn, args.task_id)

    num = args.task_id.split("-", 1)[-1].lower()  # "052" from "TASK-052"
    artifacts_dir = ROOT / "artifacts"
    handoffs_dir = ROOT / "handoffs"

    reviews = sorted((artifacts_dir / "reviews").glob(f"task{num}*.md"))
    releases = sorted((artifacts_dir / "releases").glob(f"task-{num}*.md"))
    handoffs = sorted(handoffs_dir.glob(f"*TASK-{num.upper()}*.md"))

    events: list[dict] = []
    if args.event_log.exists():
        with args.event_log.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if ev.get("task_id") == args.task_id:
                    events.append(ev)

    sep = "─" * 60
    print(f"\n{sep}")
    print(f"  TASK LOG  {args.task_id}: {payload['title']}")
    print(sep)

    print(f"\nStatus   : {payload['status']}")
    print(f"Owner    : {payload['owner']}")
    print(f"Type     : {payload['task_type']} / {payload['role']}")
    print(f"Created  : {payload['created_at']}")
    print(f"Updated  : {payload['updated_at']}")

    if payload.get("dependencies"):
        print(f"Deps     : {', '.join(payload['dependencies'])}")

    print("\nAcceptance criteria:")
    for i, c in enumerate(payload.get("acceptance_criteria", []), 1):
        print(f"  {i}. {c}")

    print(f"\n{sep}")
    print(f"  EVENT TIMELINE  ({len(events)} events)")
    print(sep)
    if events:
        for ev in events:
            ts = ev.get("created_at", "?")
            sender = ev.get("sender", "?")
            etype = ev.get("type", "?")
            summary = ev.get("summary", "")
            paths = ev.get("artifact_paths", [])
            print(f"\n[{ts}] {etype}  ({sender})")
            print(f"  {summary}")
            for p in paths:
                print(f"    → {p}")
    else:
        print("  (no events recorded)")

    if reviews or releases or handoffs:
        print(f"\n{sep}")
        print("  LINKED ARTIFACTS")
        print(sep)
        for p in reviews:
            print(f"  review   : MAP_System/artifacts/reviews/{p.name}")
        for p in releases:
            print(f"  release  : MAP_System/artifacts/releases/{p.name}")
        for p in handoffs:
            print(f"  handoff  : MAP_System/handoffs/{p.name}")

    print(f"\n{sep}\n")
    return 0


def release_task_state(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        str(RELEASE_TASK),
        args.task_id,
        "--released-by",
        args.released_by,
        "--checklist",
        str(args.checklist),
        "--db",
        str(args.db),
        "--event-log",
        str(args.event_log),
    ]
    if args.summary:
        cmd.extend(["--summary", args.summary])
    if args.output_dir:
        cmd.extend(["--output-dir", str(args.output_dir)])
    subprocess.run(cmd, cwd=ROOT.parent, check=True)
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--event-log", type=Path, default=EVENT_LOG)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("--task-id", required=True, help="Task ID or 'auto' for the next atomic TASK-NNN")
    create.add_argument("--title", required=True)
    create.add_argument("--owner", required=True)
    create.add_argument("--description", default="")
    create.add_argument("--task-type", default="implementation")
    create.add_argument("--role", default="implementer")
    create.add_argument("--priority", type=int, default=3)
    create.add_argument("--required-agent")
    create.add_argument("--max-attempts", type=int, default=3)
    create.add_argument("--depends-on", nargs="*", default=[])
    create.add_argument("--output-path", action="append", default=[])
    create.add_argument("--criterion", action="append", default=[])
    create.add_argument("--actor", default="map-task")
    create.set_defaults(func=create_task)

    approve = sub.add_parser("approve")
    approve.add_argument("task_id")
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--review-record", type=Path, default=None,
                         help="Path to review record file (HPOM-004: required for APPROVED status)")
    approve.set_defaults(func=lambda args: set_review_state(args, approved=True))

    reject = sub.add_parser("reject")
    reject.add_argument("task_id")
    reject.add_argument("--reviewer", required=True)
    reject.add_argument("--reason", required=True)
    reject.set_defaults(func=lambda args: set_review_state(args, approved=False))

    rework = sub.add_parser("rework", help="Return a CHANGES_REQUESTED task to READY for revision")
    rework.add_argument("task_id")
    rework.add_argument("--actor", required=True)
    rework.add_argument("--reason", required=True)
    rework.set_defaults(func=rework_task)

    release = sub.add_parser("release")
    release.add_argument("task_id")
    release.add_argument("--released-by", required=True)
    release.add_argument("--checklist", type=Path, required=True)
    release.add_argument("--summary", default="")
    release.set_defaults(func=release_task_state)

    show = sub.add_parser("show")
    show.add_argument("task_id")
    show.set_defaults(func=show_task)

    log = sub.add_parser("log", help="Print a readable timeline for a task")
    log.add_argument("task_id")
    log.set_defaults(func=log_task)

    return parser.parse_args()


def main() -> int:
    try:
        args = parse_args()
        return args.func(args)
    except (sqlite3.Error, subprocess.CalledProcessError, UsageError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
