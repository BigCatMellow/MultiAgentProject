#!/usr/bin/env python3
"""Validate structural shape of tasks/TASK-NNN.json files.

`promote_task.py` validates 8 HPOM fields at READY-promotion time, but
nothing checks the JSON's own structural correctness (required keys present,
correct types, status drawn from the canonical vocabulary, list-shaped
fields actually lists of strings). This fills that gap
(notes/command-center-later.md, source-mining audit TASK-196).

Usage:
    python3 MAP_System/scripts/validate_task_schema.py [--tasks-dir PATH]

Exit codes:
    0  all task files structurally valid
    1  one or more files have a structural defect
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TASKS_DIR = ROOT / "tasks"

TASK_ID_RE = re.compile(r"^TASK-\d{3,}$")

REQUIRED_STRING_FIELDS = ["task_id", "title", "task_type", "role", "status", "owner", "description"]
REQUIRED_LIST_FIELDS = ["dependencies", "input_paths", "output_paths", "acceptance_criteria"]

# Canonical status vocabulary, per validate_task_graph.py's terminal/active
# sets and promote_task.py's CONFLICT/READY handling.
CANONICAL_STATUSES = {
    "READY", "IN_PROGRESS", "SUBMITTED", "REVIEW", "CHANGES_REQUESTED",
    "BLOCKED", "CONFLICT", "APPROVED", "RELEASED", "DONE", "RETIRED",
}


def check_task(task_id_from_filename: str, data: object) -> list[str]:
    errors: list[str] = []

    if not isinstance(data, dict):
        return [f"{task_id_from_filename}: task file is not a JSON object"]

    for field in REQUIRED_STRING_FIELDS:
        if field not in data:
            errors.append(f"{task_id_from_filename}: missing required field {field!r}")
        elif not isinstance(data[field], str) or not data[field].strip():
            errors.append(f"{task_id_from_filename}: field {field!r} must be a non-empty string")

    for field in REQUIRED_LIST_FIELDS:
        if field not in data:
            errors.append(f"{task_id_from_filename}: missing required field {field!r}")
            continue
        value = data[field]
        if not isinstance(value, list):
            errors.append(f"{task_id_from_filename}: field {field!r} must be a list")
        elif not all(isinstance(item, str) for item in value):
            errors.append(f"{task_id_from_filename}: field {field!r} must be a list of strings")

    task_id = data.get("task_id")
    if isinstance(task_id, str):
        if not TASK_ID_RE.match(task_id):
            errors.append(f"{task_id_from_filename}: task_id {task_id!r} does not match TASK-NNN shape")
        if task_id != task_id_from_filename:
            errors.append(
                f"{task_id_from_filename}: task_id field {task_id!r} does not match filename"
            )

    status = data.get("status")
    if isinstance(status, str) and status not in CANONICAL_STATUSES:
        errors.append(
            f"{task_id_from_filename}: status {status!r} is not in the canonical vocabulary "
            f"({sorted(CANONICAL_STATUSES)})"
        )

    return errors


def validate(tasks_dir: Path) -> list[str]:
    errors: list[str] = []
    if not tasks_dir.exists():
        return [f"missing task directory: {tasks_dir}"]

    for path in sorted(tasks_dir.glob("TASK-*.json")):
        task_id_from_filename = path.stem
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{task_id_from_filename}: invalid JSON ({exc})")
            continue
        errors.extend(check_task(task_id_from_filename, data))

    return errors


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks-dir", default=str(DEFAULT_TASKS_DIR))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    errors = validate(Path(args.tasks_dir))
    if errors:
        print("Task schema validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Task schema validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
