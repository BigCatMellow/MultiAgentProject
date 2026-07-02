#!/usr/bin/env python3
"""Regression tests for MAP runner task classification."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from MAP_System.graph.runner import evaluate_tasks


def test_blocked_task_never_becomes_ready_when_dependencies_are_done():
    state = {
        "tasks": [
            {
                "task_id": "TASK-001",
                "status": "APPROVED",
                "dependencies": [],
                "task_type": "maintenance",
                "role": "state_steward",
                "title": "Done dependency",
                "description": "",
                "acceptance_criteria": [],
            },
            {
                "task_id": "TASK-002",
                "status": "BLOCKED",
                "dependencies": ["TASK-001"],
                "task_type": "maintenance",
                "role": "state_steward",
                "title": "Duplicate task",
                "description": "Blocked as duplicate; should not route to claim.",
                "acceptance_criteria": [],
            },
        ],
        "agents": {},
    }

    result = evaluate_tasks(state)

    assert result["ready_tasks"] == []
    assert result["ready_tasks_waiting_for_agent"] == []
    assert result["blocked_tasks"] == ["TASK-002"]


if __name__ == "__main__":
    test_blocked_task_never_becomes_ready_when_dependencies_are_done()
    print("PASS runner task classification")
