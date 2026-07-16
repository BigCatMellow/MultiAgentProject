#!/usr/bin/env python3
"""Runner integration tests for TASK-163 pre-dispatch policy gates."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from MAP_System.graph.runner import choose_route, evaluate_tasks, route_policy_gate  # noqa: E402


def base_state(task):
    return {
        "tasks": [task],
        "agents": {},
        "halt_state": {"state": "clear"},
        "events": [],
    }


def base_task(**overrides):
    task = {
        "task_id": "TASK-P",
        "status": "READY",
        "dependencies": [],
        "task_type": "implementation",
        "role": "engineer",
        "title": "Safe task",
        "description": "Implement a bounded change.",
        "output_paths": ["MAP_System/scripts/example.py"],
        "acceptance_criteria": ["works"],
    }
    task.update(overrides)
    return task


def test_policy_required_task_routes_to_visible_policy_gate() -> None:
    state = evaluate_tasks(base_state(base_task(description="Needs force push. force push")))

    assert state["ready_tasks"] == []
    assert state["blocked_tasks"] == ["TASK-P"]
    assert state["policy_gated_tasks"] == ["TASK-P"]
    assert state["policy_results"][0]["decision"] == "require_approval"
    assert "REQUIRE_CORE_DESTRUCTIVE_APPROVAL" in state["policy_results"][0]["reasons"]
    assert choose_route(state) == "policy_gate"

    routed = route_policy_gate(state)
    assert routed["next_route"] == "policy_gate"
    assert "TASK-P requires pre-dispatch approval" in routed["recommended_action"]


def test_rejected_helper_work_is_not_recommended_as_helper_candidate() -> None:
    state = evaluate_tasks(base_state(base_task(task_type="review", role="reviewer", title="Final review")))

    assert state["ready_tasks"] == ["TASK-P"]
    assert state["helper_candidate_tasks"] == []
    helper_results = [result for result in state["policy_results"] if result["candidate_worker"] == "visible-helper"]
    assert helper_results
    assert helper_results[0]["decision"] == "reject"
    assert "REJECT_HELPER_FINAL_REVIEW" in helper_results[0]["reasons"]


def test_allowed_task_remains_ready_for_normal_dispatch() -> None:
    state = evaluate_tasks(base_state(base_task()))

    assert state["ready_tasks"] == ["TASK-P"]
    assert state["policy_gated_tasks"] == []
    assert state["policy_rejected_tasks"] == []
    assert choose_route(state) == "claim_or_assign"


def main() -> int:
    tests = [
        test_policy_required_task_routes_to_visible_policy_gate,
        test_rejected_helper_work_is_not_recommended_as_helper_candidate,
        test_allowed_task_remains_ready_for_normal_dispatch,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
