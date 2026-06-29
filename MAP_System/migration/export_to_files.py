#!/usr/bin/env python3
"""Export MAP_System/map.db task state back to JSON files."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "map.db"
TASKS_DIR = ROOT / "tasks"
GRAPH_PATH = ROOT / "workflow" / "task_graph.json"
AGENTS_PATH = ROOT / "agents" / "status.json"
SYSTEM_AGENTS = {"command-center", "langgraph-runner", "reconcile"}


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_task_values(conn: sqlite3.Connection, sql: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for row in conn.execute(sql):
        values.setdefault(row["task_id"], []).append(row["value"])
    return values


def load_tasks(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    conn.row_factory = sqlite3.Row
    dependencies = load_task_values(
        conn,
        "SELECT task_id, depends_on AS value FROM task_dependencies ORDER BY task_id, depends_on",
    )
    output_paths = load_task_values(
        conn,
        "SELECT task_id, path AS value FROM task_output_paths ORDER BY task_id, path",
    )
    criteria = load_task_values(
        conn,
        "SELECT task_id, criterion AS value FROM task_acceptance_criteria ORDER BY task_id, id",
    )
    rows = conn.execute(
        """
        SELECT task_id, title, task_type, role, status, owner, description
        FROM tasks
        ORDER BY task_id
        """
    ).fetchall()
    tasks: list[dict[str, Any]] = []
    for row in rows:
        task = dict(row)
        task["dependencies"] = dependencies.get(row["task_id"], [])
        task["output_paths"] = output_paths.get(row["task_id"], [])
        task["acceptance_criteria"] = criteria.get(row["task_id"], [])
        tasks.append(task)
    return tasks


def load_agents(conn: sqlite3.Connection) -> dict[str, Any]:
    conn.row_factory = sqlite3.Row
    agents: dict[str, Any] = {}
    rows = conn.execute(
        """
        SELECT agent_id, status, reason, resume_after, agent_type
        FROM agents
        ORDER BY agent_id
        """
    ).fetchall()
    for row in rows:
        if row["agent_type"] == "system" or row["agent_id"] in SYSTEM_AGENTS:
            continue
        agents[row["agent_id"]] = {
            "status": row["status"],
            "reason": row["reason"],
            "resume_after": row["resume_after"],
            "notes": existing_agent_note(row["agent_id"]),
        }
    return {"agents": agents}


def existing_agent_note(agent_id: str) -> str:
    current = read_json(AGENTS_PATH, {"agents": {}})
    return current.get("agents", {}).get(agent_id, {}).get("notes", "")


def task_file_payload(task: dict[str, Any], *, tasks_dir: Path = TASKS_DIR) -> dict[str, Any]:
    existing = read_json(tasks_dir / f"{task['task_id']}.json", {})
    payload = dict(existing)
    payload.update({
        "task_id": task["task_id"],
        "title": task["title"],
        "task_type": task["task_type"],
        "role": task["role"],
        "status": task["status"],
        "dependencies": task["dependencies"],
        "owner": task["owner"],
        "description": task.get("description") or existing.get("description", ""),
        "input_paths": existing.get("input_paths", []),
        "output_paths": task["output_paths"],
        "acceptance_criteria": task["acceptance_criteria"],
    })
    return payload


def graph_payload(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    existing = read_json(GRAPH_PATH, {"project_id": "MAP-BOOTSTRAP-20260617", "approval_gates": []})
    return {
        "project_id": existing.get("project_id", "MAP-BOOTSTRAP-20260617"),
        "tasks": [
            {
                "task_id": task["task_id"],
                "title": task["title"],
                "task_type": task["task_type"],
                "role": task["role"],
                "status": task["status"],
                "dependencies": task["dependencies"],
                "owner": task["owner"],
                "output_paths": task["output_paths"],
                "acceptance_criteria": task["acceptance_criteria"],
            }
            for task in tasks
        ],
        "approval_gates": existing.get("approval_gates", []),
    }


def write_json(path: Path, payload: Any, *, dry_run: bool) -> bool:
    text = json.dumps(payload, indent=2) + "\n"
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old == text:
        return False
    if not dry_run:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-dir", type=Path, default=None,
                        help="Write tasks/, workflow/, agents/ under this dir instead of MAP_System/")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = args.db if args.db.is_absolute() else Path.cwd() / args.db
    out = args.output_dir if args.output_dir else ROOT
    tasks_dir = out / "tasks"
    graph_path = out / "workflow" / "task_graph.json"
    agents_path = out / "agents" / "status.json"
    written = 0
    unchanged = 0

    with sqlite3.connect(db_path) as conn:
        tasks = load_tasks(conn)
        agents = load_agents(conn)

    for task in tasks:
        changed = write_json(
            tasks_dir / f"{task['task_id']}.json",
            task_file_payload(task, tasks_dir=tasks_dir),
            dry_run=args.dry_run,
        )
        written += int(changed)
        unchanged += int(not changed)

    for path, payload in [
        (graph_path, graph_payload(tasks)),
        (agents_path, agents),
    ]:
        changed = write_json(path, payload, dry_run=args.dry_run)
        written += int(changed)
        unchanged += int(not changed)

    mode = "dry_run" if args.dry_run else "written"
    print(f"mode={mode}")
    print(f"files_written={written}")
    print(f"files_unchanged={unchanged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
