#!/usr/bin/env python3
"""Regression tests for MAP runner task classification."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from MAP_System.graph.runner import evaluate_tasks


def test_paid_halt_suppresses_paid_ready_task_but_keeps_review_ready():
    state = {
        "halt_state": {
            "halt_id": "HALT-test",
            "state": "halt_paid_dispatch",
            "reason": "spend_rate_breaker",
            "set_by": "cost-governance",
            "set_at": "2026-07-14T00:00:00Z",
            "scope": "paid",
            "target": None,
            "clear_requires": "command_center",
            "cleared_by": None,
            "cleared_at": None,
            "clear_reason": "",
            "related_event_ids": [],
        },
        "tasks": [
            {
                "task_id": "TASK-001",
                "status": "READY",
                "dependencies": [],
                "task_type": "implementation",
                "role": "implementer",
                "title": "Paid work",
                "description": "",
                "acceptance_criteria": [],
            },
            {
                "task_id": "TASK-002",
                "status": "READY",
                "dependencies": [],
                "task_type": "review",
                "role": "reviewer",
                "title": "Review work",
                "description": "",
                "acceptance_criteria": [],
            },
        ],
        "agents": {},
    }

    result = evaluate_tasks(state)

    assert result["ready_tasks"] == ["TASK-002"]
    assert result["dispatch_blocked_tasks"] == ["TASK-001"]
    assert result["blocked_tasks"] == ["TASK-001"]


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


def test_released_dependency_satisfies_ready_task():
    state = {
        "tasks": [
            {
                "task_id": "TASK-001",
                "status": "RELEASED",
                "dependencies": [],
                "task_type": "architecture",
                "role": "implementer",
                "title": "Released dependency",
                "description": "",
                "acceptance_criteria": [],
            },
            {
                "task_id": "TASK-002",
                "status": "READY",
                "dependencies": ["TASK-001"],
                "task_type": "implementation",
                "role": "implementer",
                "title": "Ready follow-up",
                "description": "",
                "acceptance_criteria": [],
            },
        ],
        "agents": {},
    }

    result = evaluate_tasks(state)

    assert result["done_task_ids"] == ["TASK-001"]
    assert result["ready_tasks"] == ["TASK-002"]
    assert result["blocked_tasks"] == []


def test_retired_dependency_does_not_satisfy_ready_task():
    state = {
        "tasks": [
            {
                "task_id": "TASK-001",
                "status": "RETIRED",
                "dependencies": [],
                "task_type": "maintenance",
                "role": "state_steward",
                "title": "Retired duplicate",
                "description": "",
                "acceptance_criteria": [],
            },
            {
                "task_id": "TASK-002",
                "status": "READY",
                "dependencies": ["TASK-001"],
                "task_type": "implementation",
                "role": "implementer",
                "title": "Dependent follow-up",
                "description": "",
                "acceptance_criteria": [],
            },
        ],
        "agents": {},
    }

    result = evaluate_tasks(state)

    assert result["done_task_ids"] == []
    assert result["ready_tasks"] == []
    assert result["blocked_tasks"] == ["TASK-002"]


if __name__ == "__main__":
    test_paid_halt_suppresses_paid_ready_task_but_keeps_review_ready()
    print("PASS test_paid_halt_suppresses_paid_ready_task_but_keeps_review_ready")
    test_blocked_task_never_becomes_ready_when_dependencies_are_done()
    print("PASS test_blocked_task_never_becomes_ready_when_dependencies_are_done")
    test_released_dependency_satisfies_ready_task()
    print("PASS test_released_dependency_satisfies_ready_task")
    test_retired_dependency_does_not_satisfy_ready_task()
    print("PASS test_retired_dependency_does_not_satisfy_ready_task")
    print("PASS runner task classification")
