#!/usr/bin/env python3
"""Validate that SQLite task state matches the JSON file mirrors."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "map.db"

ACTIVE_STATUSES = {
    "NEEDS_SHAPING",
    "READY",
    "IN_PROGRESS",
    "SUBMITTED",
    "CHANGES_REQUESTED",
    "APPROVED",
}
SCALAR_FIELDS = ("title", "task_type", "role", "status", "owner")
LIST_FIELDS = ("dependencies", "output_paths", "acceptance_criteria")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def list_values(conn: sqlite3.Connection, sql: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for row in conn.execute(sql):
        values.setdefault(row["task_id"], []).append(row["value"])
    return values


def load_db_tasks(db_path: Path) -> dict[str, dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        dependencies = list_values(
            conn,
            "SELECT task_id, depends_on AS value FROM task_dependencies ORDER BY task_id, depends_on",
        )
        output_paths = list_values(
            conn,
            "SELECT task_id, path AS value FROM task_output_paths ORDER BY task_id, path",
        )
        criteria = list_values(
            conn,
            "SELECT task_id, criterion AS value FROM task_acceptance_criteria ORDER BY task_id, id",
        )
        rows = conn.execute(
            """
            SELECT task_id, title, task_type, role, status, owner
            FROM tasks
            ORDER BY task_id
            """
        ).fetchall()

    tasks: dict[str, dict[str, Any]] = {}
    for row in rows:
        task = dict(row)
        task_id = task["task_id"]
        task["dependencies"] = dependencies.get(task_id, [])
        task["output_paths"] = output_paths.get(task_id, [])
        task["acceptance_criteria"] = criteria.get(task_id, [])
        tasks[task_id] = task
    return tasks


def normalize_list(field: str, values: Any) -> list[str]:
    if values is None:
        return []
    if not isinstance(values, list):
        return [f"<non-list:{type(values).__name__}>"]
    if field in {"dependencies", "output_paths"}:
        return sorted(str(value) for value in values)
    return [str(value) for value in values]


def compare_task(
    *,
    label: str,
    task_id: str,
    expected: dict[str, Any],
    actual: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for field in SCALAR_FIELDS:
        if actual.get(field) != expected.get(field):
            errors.append(
                f"{label} {task_id} {field} mismatch: "
                f"db={expected.get(field)!r} mirror={actual.get(field)!r}"
            )
    for field in LIST_FIELDS:
        expected_values = normalize_list(field, expected.get(field))
        actual_values = normalize_list(field, actual.get(field))
        if actual_values != expected_values:
            errors.append(
                f"{label} {task_id} {field} mismatch: "
                f"db={expected_values!r} mirror={actual_values!r}"
            )
    return errors


def validate(db_path: Path, root: Path, *, active_only: bool = False) -> list[str]:
    errors: list[str] = []
    db_tasks = load_db_tasks(db_path)
    if active_only:
        db_tasks = {
            task_id: task
            for task_id, task in db_tasks.items()
            if task.get("status") in ACTIVE_STATUSES
        }

    graph_path = root / "workflow" / "task_graph.json"
    tasks_dir = root / "tasks"
    if not graph_path.exists():
        return [f"missing task graph mirror: {graph_path}"]
    if not tasks_dir.exists():
        return [f"missing task mirror directory: {tasks_dir}"]

    graph = load_json(graph_path)
    graph_tasks = {
        task["task_id"]: task
        for task in graph.get("tasks", [])
        if isinstance(task, dict) and task.get("task_id")
    }

    for task_id, expected in db_tasks.items():
        task_file = tasks_dir / f"{task_id}.json"
        if not task_file.exists():
            errors.append(f"missing task file mirror for {task_id}: {task_file}")
        else:
            errors.extend(
                compare_task(
                    label="task-file",
                    task_id=task_id,
                    expected=expected,
                    actual=load_json(task_file),
                )
            )

        graph_task = graph_tasks.get(task_id)
        if graph_task is None:
            errors.append(f"workflow/task_graph.json missing {task_id}")
        else:
            errors.extend(
                compare_task(
                    label="task-graph",
                    task_id=task_id,
                    expected=expected,
                    actual=graph_task,
                )
            )

    extra_files = {
        path.stem
        for path in tasks_dir.glob("TASK-*.json")
        if path.stem not in db_tasks
    }
    for task_id in sorted(extra_files):
        errors.append(f"task file mirror has no SQLite task: {task_id}")

    extra_graph = set(graph_tasks) - set(db_tasks)
    for task_id in sorted(extra_graph):
        errors.append(f"task graph mirror has no SQLite task: {task_id}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--root", type=Path, default=ROOT, help="Directory containing tasks/ and workflow/")
    parser.add_argument("--active-only", action="store_true", help="Only compare editable/review/release states")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable result")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    db_path = args.db if args.db.is_absolute() else Path.cwd() / args.db
    root = args.root if args.root.is_absolute() else Path.cwd() / args.root
    errors = validate(db_path, root, active_only=args.active_only)
    if args.json:
        print(json.dumps({"ok": not errors, "errors": errors}, indent=2))
    elif errors:
        print("Task mirror validation failed:")
        for error in errors:
            print(f"- {error}")
    else:
        print("Task mirror validation passed.")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
