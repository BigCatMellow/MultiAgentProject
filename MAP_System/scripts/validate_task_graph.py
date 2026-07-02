#!/usr/bin/env python3
"""Validate the file-backed MAP task graph."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GRAPH_PATH = ROOT / "workflow" / "task_graph.json"

SHARED_OUTPUT_PATHS = {
    "MAP_System/events/events.jsonl",
    "MAP_System/emergence/INDEX.md",
    "MAP_System/workflow/task_graph.json",
}


def is_shared_output(path: str) -> bool:
    normalized = path.rstrip("/")
    return normalized in SHARED_OUTPUT_PATHS


def load_graph() -> dict:
    with GRAPH_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def detect_cycle(tasks: dict[str, dict]) -> list[str] | None:
    visiting: set[str] = set()
    visited: set[str] = set()
    stack: list[str] = []

    def visit(task_id: str) -> list[str] | None:
        if task_id in visited:
            return None
        if task_id in visiting:
            return stack[stack.index(task_id):] + [task_id]
        visiting.add(task_id)
        stack.append(task_id)
        for dependency in tasks[task_id].get("dependencies", []):
            if dependency not in tasks:
                continue  # already reported as unknown dependency
            cycle = visit(dependency)
            if cycle:
                return cycle
        stack.pop()
        visiting.remove(task_id)
        visited.add(task_id)
        return None

    for task_id in tasks:
        cycle = visit(task_id)
        if cycle:
            return cycle
    return None


def validate(graph: dict) -> list[str]:
    errors: list[str] = []
    raw_tasks = graph.get("tasks", [])
    task_ids = [task.get("task_id") for task in raw_tasks]

    if not graph.get("project_id"):
        errors.append("Missing project_id")
    if not raw_tasks:
        errors.append("No tasks defined")
    if len(task_ids) != len(set(task_ids)):
        errors.append("Duplicate task_id found")

    tasks = {task["task_id"]: task for task in raw_tasks if task.get("task_id")}

    for task in raw_tasks:
        task_id = task.get("task_id", "<missing>")
        for dependency in task.get("dependencies", []):
            if dependency not in tasks:
                errors.append(f"{task_id} has unknown dependency {dependency}")
        if not task.get("acceptance_criteria"):
            errors.append(f"{task_id} has no acceptance criteria")
        if not task.get("output_paths"):
            errors.append(f"{task_id} has no output_paths")
        task_file = ROOT / "tasks" / f"{task_id}.json"
        if not task_file.exists():
            errors.append(f"{task_id} has no matching task file at {task_file.relative_to(ROOT)}")

    terminal = {"DONE", "APPROVED", "RELEASED"}
    active = {"READY", "IN_PROGRESS", "SUBMITTED", "REVIEW", "CHANGES_REQUESTED"}
    stalled = [t for t in tasks.values() if t.get("status") not in terminal | active]
    all_done = all(t.get("status") in terminal for t in tasks.values())
    if not all_done and not any(t.get("status") in active for t in tasks.values()):
        errors.append(
            f"Graph is stalled: {len(stalled)} task(s) are BACKLOG/BLOCKED with nothing active or ready"
        )

    cycle = detect_cycle(tasks) if tasks else None
    if cycle:
        errors.append("Dependency cycle: " + " -> ".join(cycle))

    active_outputs: dict[str, str] = {}
    for task in raw_tasks:
        if task.get("status") in terminal | {"BLOCKED"}:
            continue
        for output_path in task.get("output_paths", []):
            if is_shared_output(output_path):
                continue
            owner = active_outputs.setdefault(output_path, task["task_id"])
            if owner != task["task_id"]:
                errors.append(f"Output path collision: {output_path} owned by {owner} and {task['task_id']}")

    return errors


def main() -> int:
    errors = validate(load_graph())
    if errors:
        print("Task graph validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Task graph validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
