#!/usr/bin/env python3
"""Tests for shared/generated task output handling."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_task_graph.py"
spec = importlib.util.spec_from_file_location("validate_task_graph", SCRIPT)
assert spec and spec.loader
validate_task_graph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_task_graph)


def graph_with_outputs(path_a: str, path_b: str) -> dict:
    return {
        "project_id": "TEST",
        "tasks": [
            {
                "task_id": "TASK-SHARED-1",
                "status": "READY",
                "dependencies": [],
                "acceptance_criteria": ["one"],
                "output_paths": [path_a],
            },
            {
                "task_id": "TASK-SHARED-2",
                "status": "READY",
                "dependencies": [],
                "acceptance_criteria": ["two"],
                "output_paths": [path_b],
            },
        ],
    }


def test_shared_generated_outputs_do_not_collide() -> None:
    errors = validate_task_graph.validate(
        graph_with_outputs("MAP_System/events/events.jsonl", "MAP_System/events/events.jsonl")
    )
    assert not [e for e in errors if "Output path collision" in e]


def test_normal_outputs_still_collide() -> None:
    errors = validate_task_graph.validate(graph_with_outputs("same.md", "same.md"))
    assert any("Output path collision: same.md" in e for e in errors)


def main() -> int:
    for test in [test_shared_generated_outputs_do_not_collide, test_normal_outputs_still_collide]:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
