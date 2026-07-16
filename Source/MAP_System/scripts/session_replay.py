#!/usr/bin/env python3
"""Build and query a local MAP session replay read model.

The replay database is derived state. It reads MAP canonical sources and writes
only the disposable SQLite index path supplied with --index.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DEFAULT_INDEX = ROOT / "runtime" / "session_replay.sqlite"
DEFAULT_EVENT_LOG = ROOT / "events" / "events.jsonl"
DEFAULT_TASK_DIR = ROOT / "tasks"
DEFAULT_DB = ROOT / "map.db"


SCHEMA = """
CREATE TABLE source_snapshots (
    source TEXT PRIMARY KEY,
    locator TEXT NOT NULL,
    size_bytes INTEGER,
    mtime_ns INTEGER,
    checksum TEXT,
    high_water TEXT,
    indexed_at TEXT NOT NULL
);

CREATE TABLE replay_events (
    replay_id TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    created_at TEXT,
    kind TEXT NOT NULL,
    task_id TEXT,
    trace_id TEXT,
    actor TEXT,
    action TEXT,
    target TEXT,
    thread TEXT,
    summary TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE INDEX idx_replay_task ON replay_events(task_id, created_at, replay_id);
CREATE INDEX idx_replay_trace ON replay_events(trace_id, created_at, replay_id);
CREATE INDEX idx_replay_actor ON replay_events(actor, created_at, replay_id);

CREATE TABLE task_index (
    task_id TEXT PRIMARY KEY,
    status TEXT,
    owner TEXT,
    claimed_by TEXT,
    attempt INTEGER,
    max_attempts INTEGER,
    output_paths_json TEXT NOT NULL,
    criteria_json TEXT NOT NULL,
    title TEXT,
    description TEXT
);

CREATE TABLE agent_index (
    agent_id TEXT PRIMARY KEY,
    last_seen_at TEXT,
    observed_sources_json TEXT NOT NULL
);

CREATE TABLE links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_ref TEXT NOT NULL,
    to_ref TEXT NOT NULL,
    link_type TEXT NOT NULL
);

CREATE TABLE drift_findings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    severity TEXT NOT NULL,
    source TEXT NOT NULL,
    code TEXT NOT NULL,
    detail TEXT NOT NULL
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def file_checksum(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_snapshot(path: Path, *, source: str, high_water: str) -> tuple:
    if not path.exists():
        return (source, str(path), None, None, None, high_water, utc_now())
    stat = path.stat()
    return (
        source,
        str(path),
        stat.st_size,
        stat.st_mtime_ns,
        file_checksum(path),
        high_water,
        utc_now(),
    )


def connect_index(index_path: Path) -> sqlite3.Connection:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(index_path)
    conn.row_factory = sqlite3.Row
    return conn


def reset_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS source_snapshots;
        DROP TABLE IF EXISTS replay_events;
        DROP TABLE IF EXISTS task_index;
        DROP TABLE IF EXISTS agent_index;
        DROP TABLE IF EXISTS links;
        DROP TABLE IF EXISTS drift_findings;
        """
    )
    conn.executescript(SCHEMA)


def load_db_tasks(db_path: Path) -> dict[str, dict[str, Any]]:
    if not db_path.exists():
        return {}
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT task_id, title, description, status, owner, claimed_by, attempt, max_attempts
            FROM tasks
            ORDER BY task_id
            """
        ).fetchall()
    return {row["task_id"]: dict(row) for row in rows}


def load_task_files(task_dir: Path) -> tuple[dict[str, dict[str, Any]], list[dict[str, str]]]:
    tasks: dict[str, dict[str, Any]] = {}
    drift: list[dict[str, str]] = []
    if not task_dir.exists():
        drift.append({"severity": "warn", "source": "task_json", "code": "task_dir_missing", "detail": str(task_dir)})
        return tasks, drift
    for path in sorted(task_dir.glob("TASK-*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            drift.append({
                "severity": "error",
                "source": "task_json",
                "code": "task_json_parse_error",
                "detail": f"{path}: {exc}",
            })
            continue
        task_id = payload.get("task_id") or path.stem
        tasks[str(task_id)] = payload
    return tasks, drift


def run_mirror_validation(db_path: Path, root: Path) -> tuple[bool, str]:
    script = ROOT / "scripts" / "validate_task_mirrors.py"
    result = subprocess.run(
        [sys.executable, str(script), "--db", str(db_path), "--root", str(root)],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return result.returncode == 0, (result.stdout + result.stderr).strip()


def derive_actor(event: dict[str, Any]) -> str | None:
    value = event.get("actor") or event.get("sender") or event.get("agent")
    return str(value) if value is not None and str(value).strip() else None


def normalize_event(line_no: int, event: dict[str, Any]) -> dict[str, Any]:
    kind = event.get("type") or event.get("event_type") or "UNKNOWN"
    created_at = event.get("created_at") or event.get("timestamp")
    summary = event.get("summary") or event.get("text") or ""
    return {
        "replay_id": f"map-events:{line_no}",
        "source": "map_events_jsonl",
        "source_event_id": str(line_no),
        "created_at": created_at,
        "kind": str(kind),
        "task_id": event.get("task_id"),
        "trace_id": event.get("trace_id"),
        "actor": derive_actor(event),
        "action": event.get("action") or str(kind).lower(),
        "target": event.get("target") or event.get("task_id"),
        "thread": event.get("thread"),
        "summary": str(summary),
        "payload_json": json.dumps(event, sort_keys=True, separators=(",", ":")),
    }


def is_task_reference(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("TASK-")


def insert_drift(conn: sqlite3.Connection, finding: dict[str, str]) -> None:
    conn.execute(
        """
        INSERT INTO drift_findings (severity, source, code, detail)
        VALUES (?, ?, ?, ?)
        """,
        (
            finding["severity"],
            finding["source"],
            finding["code"],
            finding["detail"],
        ),
    )


def build_index(
    *,
    index_path: Path = DEFAULT_INDEX,
    event_log: Path = DEFAULT_EVENT_LOG,
    task_dir: Path = DEFAULT_TASK_DIR,
    db_path: Path = DEFAULT_DB,
    root: Path = ROOT,
    validate_mirrors: bool = True,
) -> dict[str, Any]:
    db_tasks = load_db_tasks(db_path)
    file_tasks, task_drift = load_task_files(task_dir)
    known_tasks = set(db_tasks) | set(file_tasks)
    event_count = 0

    with connect_index(index_path) as conn:
        reset_schema(conn)

        if validate_mirrors:
            ok, detail = run_mirror_validation(db_path, root)
            if not ok:
                insert_drift(conn, {
                    "severity": "error",
                    "source": "task_mirrors",
                    "code": "mirror_validation_failed",
                    "detail": detail or "validate_task_mirrors.py failed",
                })

        for finding in task_drift:
            insert_drift(conn, finding)

        if not event_log.exists():
            insert_drift(conn, {
                "severity": "error",
                "source": "map_events_jsonl",
                "code": "event_log_missing",
                "detail": str(event_log),
            })
        else:
            for line_no, line in enumerate(event_log.read_text(encoding="utf-8").splitlines(), start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError as exc:
                    insert_drift(conn, {
                        "severity": "error",
                        "source": "map_events_jsonl",
                        "code": "malformed_event",
                        "detail": f"line {line_no}: {exc}",
                    })
                    continue
                event = normalize_event(line_no, payload)
                conn.execute(
                    """
                    INSERT INTO replay_events
                        (replay_id, source, source_event_id, created_at, kind, task_id,
                         trace_id, actor, action, target, thread, summary, payload_json)
                    VALUES
                        (:replay_id, :source, :source_event_id, :created_at, :kind, :task_id,
                         :trace_id, :actor, :action, :target, :thread, :summary, :payload_json)
                    """,
                    event,
                )
                event_count += 1
                task_id = event.get("task_id")
                if is_task_reference(task_id) and task_id not in known_tasks:
                    insert_drift(conn, {
                        "severity": "warn",
                        "source": "map_events_jsonl",
                        "code": "missing_task_ref",
                        "detail": f"line {line_no}: {task_id}",
                    })
                if task_id:
                    conn.execute(
                        "INSERT INTO links (from_ref, to_ref, link_type) VALUES (?, ?, ?)",
                        (event["replay_id"], f"task:{task_id}", "event_task"),
                    )
                actor = event.get("actor")
                if actor:
                    conn.execute(
                        "INSERT INTO links (from_ref, to_ref, link_type) VALUES (?, ?, ?)",
                        (event["replay_id"], f"agent:{actor}", "event_actor"),
                    )

        for task_id in sorted(known_tasks):
            db_task = db_tasks.get(task_id, {})
            file_task = file_tasks.get(task_id, {})
            conn.execute(
                """
                INSERT INTO task_index
                    (task_id, status, owner, claimed_by, attempt, max_attempts,
                     output_paths_json, criteria_json, title, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    db_task.get("status") or file_task.get("status"),
                    db_task.get("owner") or file_task.get("owner"),
                    db_task.get("claimed_by"),
                    db_task.get("attempt"),
                    db_task.get("max_attempts"),
                    json.dumps(file_task.get("output_paths", []), sort_keys=True),
                    json.dumps(file_task.get("acceptance_criteria", []), sort_keys=True),
                    db_task.get("title") or file_task.get("title"),
                    db_task.get("description") or file_task.get("description"),
                ),
            )

        agent_sources: dict[str, set[str]] = {}
        last_seen: dict[str, str] = {}
        for row in conn.execute("SELECT actor, created_at, source FROM replay_events WHERE actor IS NOT NULL"):
            agent = row["actor"]
            agent_sources.setdefault(agent, set()).add(row["source"])
            if row["created_at"] and (agent not in last_seen or row["created_at"] > last_seen[agent]):
                last_seen[agent] = row["created_at"]
        for task in db_tasks.values():
            for field in ("owner", "claimed_by"):
                agent = task.get(field)
                if agent:
                    agent_sources.setdefault(agent, set()).add("map_db")
        for agent in sorted(agent_sources):
            conn.execute(
                """
                INSERT INTO agent_index (agent_id, last_seen_at, observed_sources_json)
                VALUES (?, ?, ?)
                """,
                (agent, last_seen.get(agent), json.dumps(sorted(agent_sources[agent]))),
            )

        task_files_count = len(list(task_dir.glob("TASK-*.json"))) if task_dir.exists() else 0
        snapshots = [
            file_snapshot(event_log, source="map_events_jsonl", high_water=f"lines:{event_count}"),
            file_snapshot(db_path, source="map_db", high_water=f"tasks:{len(db_tasks)}"),
            (  # Directory snapshot.
                "task_json",
                str(task_dir),
                None,
                task_dir.stat().st_mtime_ns if task_dir.exists() else None,
                None,
                f"files:{task_files_count}",
                utc_now(),
            ),
        ]
        conn.executemany(
            """
            INSERT INTO source_snapshots
                (source, locator, size_bytes, mtime_ns, checksum, high_water, indexed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            snapshots,
        )

        drift_count = conn.execute("SELECT COUNT(*) FROM drift_findings").fetchone()[0]
        conn.commit()

    return {
        "index": str(index_path),
        "events_indexed": event_count,
        "tasks_indexed": len(known_tasks),
        "drift_findings": drift_count,
        "safe_for_mission_control": drift_count == 0,
    }


def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def index_status(index_path: Path = DEFAULT_INDEX) -> dict[str, Any]:
    if not index_path.exists():
        return {"index": str(index_path), "exists": False, "safe_for_mission_control": False}
    with connect_index(index_path) as conn:
        source_snapshots = rows_to_dicts(conn.execute("SELECT * FROM source_snapshots ORDER BY source").fetchall())
        row_counts = {
            row["source"]: row["count"]
            for row in conn.execute("SELECT source, COUNT(*) AS count FROM replay_events GROUP BY source ORDER BY source")
        }
        event_kinds = {
            row["kind"]: row["count"]
            for row in conn.execute("SELECT kind, COUNT(*) AS count FROM replay_events GROUP BY kind ORDER BY kind")
        }
        drift_findings = rows_to_dicts(
            conn.execute("SELECT severity, source, code, detail FROM drift_findings ORDER BY id").fetchall()
        )
    return {
        "index": str(index_path),
        "exists": True,
        "source_snapshots": source_snapshots,
        "row_counts": row_counts,
        "event_kinds": event_kinds,
        "drift_findings": drift_findings,
        "safe_for_mission_control": not drift_findings,
    }


def query_events(index_path: Path, where: str, params: tuple[Any, ...], limit: int) -> dict[str, Any]:
    with connect_index(index_path) as conn:
        rows = conn.execute(
            f"""
            SELECT replay_id, source, source_event_id, created_at, kind, task_id,
                   trace_id, actor, action, target, thread, summary
            FROM replay_events
            WHERE {where}
            ORDER BY COALESCE(created_at, ''), replay_id
            LIMIT ?
            """,
            params + (limit,),
        ).fetchall()
    return {"index": str(index_path), "events": rows_to_dicts(rows)}


def query_task(index_path: Path, task_id: str, limit: int) -> dict[str, Any]:
    with connect_index(index_path) as conn:
        task_row = conn.execute("SELECT * FROM task_index WHERE task_id = ?", (task_id,)).fetchone()
    payload = query_events(index_path, "task_id = ?", (task_id,), limit)
    payload["task"] = dict(task_row) if task_row else None
    return payload


def query_agent(index_path: Path, agent_id: str, limit: int) -> dict[str, Any]:
    with connect_index(index_path) as conn:
        agent_row = conn.execute("SELECT * FROM agent_index WHERE agent_id = ?", (agent_id,)).fetchone()
    payload = query_events(index_path, "actor = ?", (agent_id,), limit)
    payload["agent"] = dict(agent_row) if agent_row else None
    return payload


def query_trace(index_path: Path, trace_id: str, limit: int) -> dict[str, Any]:
    return query_events(index_path, "trace_id = ?", (trace_id,), limit)


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, default=DEFAULT_INDEX)
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Rebuild the disposable replay index")
    build.add_argument("--event-log", type=Path, default=DEFAULT_EVENT_LOG)
    build.add_argument("--task-dir", type=Path, default=DEFAULT_TASK_DIR)
    build.add_argument("--db", type=Path, default=DEFAULT_DB)
    build.add_argument("--root", type=Path, default=ROOT)
    build.add_argument("--skip-mirror-validation", action="store_true")

    sub.add_parser("status", help="Show replay index health and source snapshots")

    task = sub.add_parser("task", help="Show replay events for a task")
    task.add_argument("task_id")
    task.add_argument("--limit", type=int, default=50)

    agent = sub.add_parser("agent", help="Show replay events for an agent")
    agent.add_argument("agent_id")
    agent.add_argument("--limit", type=int, default=50)

    trace = sub.add_parser("trace", help="Show replay events for a trace ID")
    trace.add_argument("trace_id")
    trace.add_argument("--limit", type=int, default=50)

    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.command == "build":
        print_json(
            build_index(
                index_path=args.index,
                event_log=args.event_log,
                task_dir=args.task_dir,
                db_path=args.db,
                root=args.root,
                validate_mirrors=not args.skip_mirror_validation,
            )
        )
        return 0
    if args.command == "status":
        print_json(index_status(args.index))
        return 0
    if args.command == "task":
        print_json(query_task(args.index, args.task_id, args.limit))
        return 0
    if args.command == "agent":
        print_json(query_agent(args.index, args.agent_id, args.limit))
        return 0
    if args.command == "trace":
        print_json(query_trace(args.index, args.trace_id, args.limit))
        return 0
    raise AssertionError(f"unhandled command {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
