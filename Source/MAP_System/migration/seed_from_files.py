#!/usr/bin/env python3
"""Seed MAP_System/map.db from the file-backed project state."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "map.db"
SCHEMA = ROOT / "migration" / "schema.sql"
SYSTEM_AGENTS = {"command-center", "langgraph-runner", "reconcile"}


class Summary:
    def __init__(self) -> None:
        self.rows: dict[str, dict[str, int]] = defaultdict(lambda: {"inserted": 0, "skipped": 0})

    def record(self, table: str, inserted: bool) -> None:
        key = "inserted" if inserted else "skipped"
        self.rows[table][key] += 1

    def print(self) -> None:
        print("Seed summary:")
        for table in sorted(self.rows):
            row = self.rows[table]
            print(f"  {table}: inserted={row['inserted']} skipped={row['skipped']}")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize_map_path(path: str) -> str:
    if not path:
        return path
    raw = Path(path)
    if raw.is_absolute():
        try:
            return raw.relative_to(ROOT).as_posix()
        except ValueError:
            return path
    text = path.replace("\\", "/")
    if text.startswith("MAP_System/"):
        return text.removeprefix("MAP_System/")
    return text


def execute_insert(
    conn: sqlite3.Connection,
    summary: Summary,
    table: str,
    sql: str,
    params: tuple[Any, ...],
) -> None:
    cursor = conn.execute(sql, params)
    summary.record(table, cursor.rowcount == 1)


def ensure_agent(
    conn: sqlite3.Connection,
    summary: Summary,
    agent_id: str | None,
    *,
    label: str | None = None,
    agent_type: str = "core",
    status: str = "available",
    reason: str | None = None,
    resume_after: str | None = None,
    update_existing: bool = False,
) -> None:
    if not agent_id:
        return
    exists = conn.execute("SELECT 1 FROM agents WHERE agent_id = ?", (agent_id,)).fetchone()
    if exists:
        if update_existing:
            conn.execute(
                """
                UPDATE agents
                SET label = ?,
                    agent_type = ?,
                    status = ?,
                    reason = ?,
                    resume_after = ?,
                    updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                WHERE agent_id = ?
                """,
                (
                    label or agent_id.replace("-", " ").title(),
                    agent_type,
                    status,
                    reason,
                    resume_after,
                    agent_id,
                ),
            )
        summary.record("agents", False)
        return
    conn.execute(
        """
        INSERT INTO agents
            (agent_id, label, agent_type, status, reason, resume_after)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (agent_id, label or agent_id.replace("-", " ").title(), agent_type, status, reason, resume_after),
    )
    summary.record("agents", True)


def seed_agents(conn: sqlite3.Connection, summary: Summary) -> None:
    status_path = ROOT / "agents" / "status.json"
    if not status_path.exists():
        return
    for agent_id, data in load_json(status_path).get("agents", {}).items():
        ensure_agent(
            conn,
            summary,
            agent_id,
            label=agent_id.replace("-", " ").title(),
            agent_type="helper" if agent_id.startswith("helper-") else "core",
            status=data.get("status") or "available",
            reason=data.get("reason"),
            resume_after=data.get("resume_after"),
            update_existing=True,
        )


def merged_task(graph_task: dict[str, Any]) -> dict[str, Any]:
    task_id = graph_task["task_id"]
    task_file = ROOT / "tasks" / f"{task_id}.json"
    if not task_file.exists():
        return graph_task
    merged = dict(graph_task)
    merged.update(load_json(task_file))
    return merged


def seed_tasks(conn: sqlite3.Connection, summary: Summary, graph: dict[str, Any]) -> None:
    project_id = graph.get("project_id") or "default"
    tasks = [merged_task(task) for task in graph.get("tasks", [])]

    for task in tasks:
        for agent_key in ("owner", "required_agent", "claimed_by"):
            ensure_agent(conn, summary, task.get(agent_key))

    for task in tasks:
        params = (
            task["task_id"],
            project_id,
            task.get("title") or task["task_id"],
            task.get("description") or "",
            task.get("task_type") or "implementation",
            task.get("role") or "implementer",
            task.get("status") or "BACKLOG",
            int(task.get("priority") or 3),
            task.get("required_agent"),
            task.get("owner"),
            task.get("claimed_by"),
            int(task.get("attempt") or 1),
            int(task.get("max_attempts") or 3),
        )
        exists = conn.execute("SELECT 1 FROM tasks WHERE task_id = ?", (task["task_id"],)).fetchone()
        if exists:
            conn.execute(
                """
                UPDATE tasks
                SET project_id = ?,
                    title = ?,
                    description = ?,
                    task_type = ?,
                    role = ?,
                    status = ?,
                    priority = ?,
                    required_agent = ?,
                    owner = ?,
                    claimed_by = ?,
                    attempt = ?,
                    max_attempts = ?,
                    updated_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                WHERE task_id = ?
                """,
                params[1:] + (task["task_id"],),
            )
            summary.record("tasks", False)
            continue
        conn.execute(
            """
            INSERT INTO tasks
                (task_id, project_id, title, description, task_type, role, status,
                 priority, required_agent, owner, claimed_by, attempt, max_attempts)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            params,
        )
        summary.record("tasks", True)

    for task in tasks:
        task_id = task["task_id"]
        for depends_on in task.get("dependencies", []):
            execute_insert(
                conn,
                summary,
                "task_dependencies",
                "INSERT OR IGNORE INTO task_dependencies (task_id, depends_on) VALUES (?, ?)",
                (task_id, depends_on),
            )
        for output_path in task.get("output_paths", []):
            execute_insert(
                conn,
                summary,
                "task_output_paths",
                "INSERT OR IGNORE INTO task_output_paths (task_id, path) VALUES (?, ?)",
                (task_id, output_path),
            )
        for criterion in task.get("acceptance_criteria", []):
            execute_insert(
                conn,
                summary,
                "task_acceptance_criteria",
                """
                INSERT OR IGNORE INTO task_acceptance_criteria (task_id, criterion, met)
                VALUES (?, ?, ?)
                """,
                (task_id, criterion, 1 if task.get("status") == "DONE" else 0),
            )


def seed_approval_gates(conn: sqlite3.Connection, summary: Summary, graph: dict[str, Any]) -> None:
    known_tasks = {
        row[0]
        for row in conn.execute("SELECT task_id FROM tasks")
    }
    for gate in graph.get("approval_gates", []):
        required_after = gate.get("required_after")
        if required_after and required_after not in known_tasks:
            required_after = None
        execute_insert(
            conn,
            summary,
            "approval_gates",
            """
            INSERT OR IGNORE INTO approval_gates (gate_id, name, required_after_task, status)
            VALUES (?, ?, ?, ?)
            """,
            (
                gate["gate_id"],
                gate.get("name") or gate["gate_id"],
                required_after,
                gate.get("status") or "pending",
            ),
        )
        for task_id in gate.get("resume_on_approval", []):
            if task_id not in known_tasks:
                summary.record("approval_gate_resume_tasks", False)
                continue
            execute_insert(
                conn,
                summary,
                "approval_gate_resume_tasks",
                "INSERT OR IGNORE INTO approval_gate_resume_tasks (gate_id, task_id) VALUES (?, ?)",
                (gate["gate_id"], task_id),
            )


def seed_events(conn: sqlite3.Connection, summary: Summary) -> None:
    events_path = ROOT / "events" / "events.jsonl"
    if not events_path.exists():
        return
    known_tasks = {
        row[0]
        for row in conn.execute("SELECT task_id FROM tasks")
    }
    with events_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(f"{events_path}:{line_number}: invalid JSONL: {exc}") from exc
            sender = event.get("sender")
            ensure_agent(
                conn,
                summary,
                sender,
                agent_type="system" if sender in SYSTEM_AGENTS else "core",
                status="available",
            )
            event_task_id = event.get("task_id")
            if event_task_id and event_task_id not in known_tasks:
                event_task_id = None
            created_at = event.get("created_at") or event.get("timestamp")
            artifact_paths = [normalize_map_path(path) for path in event.get("artifact_paths", [])]
            event_key = (
                created_at or "",
                event.get("type") or "PROGRESS",
                event_task_id or "",
                sender or "",
                event.get("summary") or "",
            )
            existing = conn.execute(
                """
                SELECT 1
                FROM events
                WHERE created_at = ?
                  AND event_type = ?
                  AND COALESCE(task_id, '') = ?
                  AND COALESCE(sender_id, '') = ?
                  AND summary = ?
                LIMIT 1
                """,
                event_key,
            ).fetchone()
            if existing:
                summary.record("events", False)
                continue
            conn.execute(
                """
                INSERT INTO events
                    (event_type, task_id, sender_id, summary, artifact_paths, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    event.get("type") or "PROGRESS",
                    event_task_id,
                    sender,
                    event.get("summary") or "",
                    json.dumps(artifact_paths, sort_keys=True),
                    created_at,
                ),
            )
            summary.record("events", True)
    prune_duplicate_events(conn, summary)


def prune_duplicate_events(conn: sqlite3.Connection, summary: Summary) -> None:
    cursor = conn.execute(
        """
        DELETE FROM events
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM events
            GROUP BY
                created_at,
                event_type,
                COALESCE(task_id, ''),
                COALESCE(sender_id, ''),
                summary
        )
        """
    )
    if cursor.rowcount:
        summary.rows["events_deduped"]["inserted"] += cursor.rowcount


DECISION_HEADING = re.compile(r"^##\s+(DEC-\d+):\s*(.+?)\s*$", re.MULTILINE)


def seed_decisions(conn: sqlite3.Connection, summary: Summary) -> None:
    decisions_path = ROOT / "shared" / "decisions.md"
    if not decisions_path.exists():
        return
    text = decisions_path.read_text(encoding="utf-8")
    matches = list(DECISION_HEADING.finditer(text))
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[match.end() : end].strip()
        status_match = re.search(r"^Status:\s*(.+?)\s*$", body, re.MULTILINE | re.IGNORECASE)
        status = status_match.group(1).strip().lower() if status_match else "open"
        exists = conn.execute("SELECT 1 FROM decisions WHERE decision_id = ?", (match.group(1),)).fetchone()
        if exists:
            conn.execute(
                """
                UPDATE decisions
                SET title = ?,
                    body = ?,
                    status = ?
                WHERE decision_id = ?
                """,
                (match.group(2), body, status, match.group(1)),
            )
            summary.record("decisions", False)
            continue
        conn.execute(
            """
            INSERT INTO decisions (decision_id, title, body, status)
            VALUES (?, ?, ?, ?)
            """,
            (match.group(1), match.group(2), body, status),
        )
        summary.record("decisions", True)


def artifact_id_for(path: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9]+", "-", path).strip("-").lower()
    return f"artifact-{clean}"


def seed_artifacts(conn: sqlite3.Connection, summary: Summary) -> None:
    artifacts_root = ROOT / "artifacts"
    if not artifacts_root.exists():
        return
    for path in sorted(artifacts_root.rglob("*.md")):
        rel = path.relative_to(artifacts_root).as_posix()
        artifact_type = rel.split("/", 1)[0] if "/" in rel else "artifact"
        title = path.stem.replace("_", " ").replace("-", " ").title()
        execute_insert(
            conn,
            summary,
            "artifacts",
            """
            INSERT OR IGNORE INTO artifacts
                (artifact_id, task_id, artifact_type, path, title, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (artifact_id_for(rel), None, artifact_type, rel, title, "draft"),
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="SQLite database path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = args.db if args.db.is_absolute() else (Path.cwd() / args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    graph = load_json(ROOT / "workflow" / "task_graph.json")
    summary = Summary()

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        seed_agents(conn, summary)
        seed_tasks(conn, summary, graph)
        seed_approval_gates(conn, summary, graph)
        seed_events(conn, summary)
        seed_decisions(conn, summary)
        seed_artifacts(conn, summary)
        conn.commit()

    print(f"Seeded {db_path}")
    summary.print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
