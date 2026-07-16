#!/usr/bin/env python3
"""Capability whitelist tests for TASK-163 pre-dispatch policy gates."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.pre_dispatch_policy import evaluate_pre_dispatch  # noqa: E402


def base_task(**overrides):
    task = {
        "task_id": "TASK-X",
        "title": "Safe implementation",
        "description": "Implement a bounded change.",
        "task_type": "implementation",
        "role": "implementer",
        "output_paths": ["MAP_System/scripts/example.py"],
        "acceptance_criteria": ["works"],
    }
    task.update(overrides)
    return task


def decision(task, tier):
    return evaluate_pre_dispatch(task, f"tier-{tier}", worker_tier=tier)


def test_helper_cannot_take_final_review() -> None:
    result = decision(base_task(task_type="review", role="reviewer"), 2)
    assert result["decision"] == "reject"
    assert "REJECT_HELPER_FINAL_REVIEW" in result["reasons"]


def test_helper_cannot_take_final_decision() -> None:
    result = decision(base_task(task_type="decision", role="approver", title="Record decision"), 2)
    assert result["decision"] == "reject"
    assert "REJECT_HELPER_FINAL_DECISION" in result["reasons"]


def test_helper_cannot_take_broad_architecture_ownership() -> None:
    result = decision(base_task(task_type="architecture", task_tier="architecture"), 2)
    assert result["decision"] == "reject"
    assert "REJECT_HELPER_BROAD_ARCHITECTURE" in result["reasons"]


def test_helper_cannot_take_broad_rewrite() -> None:
    result = decision(base_task(broad_rewrite=True, output_paths=[f"file-{idx}.py" for idx in range(8)]), 2)
    assert result["decision"] == "reject"
    assert "REJECT_HELPER_BROAD_REWRITE" in result["reasons"]


def test_helper_cannot_take_destructive_operation() -> None:
    result = decision(base_task(destructive_action=True), 2)
    assert result["decision"] == "reject"
    assert "REJECT_HELPER_DESTRUCTIVE" in result["reasons"]


def test_helper_cannot_take_shell_network_or_canonical_mutation() -> None:
    result = decision(base_task(shell_required=True, network_required=True, canonical_map_mutation=True), 2)
    assert result["decision"] == "reject"
    assert "REJECT_HELPER_SHELL_NETWORK" in result["reasons"]
    assert "REJECT_HELPER_CANONICAL_MUTATION" in result["reasons"]


def test_local_cannot_take_shell_network_or_canonical_mutation() -> None:
    result = decision(base_task(shell_required=True, output_paths=["MAP_System/tasks/TASK-X.json"]), 3)
    assert result["decision"] == "reject"
    assert "REJECT_LOCAL_SHELL_NETWORK" in result["reasons"]
    assert "REJECT_LOCAL_CANONICAL_MUTATION" in result["reasons"]


def test_read_only_review_draft_helper_is_allowed() -> None:
    result = evaluate_pre_dispatch(
        base_task(title="Read-only review draft", description="Draft review notes only.", draft_only=True),
        "visible-helper",
        worker_tier=2,
        assignment_mode="helper_draft",
    )
    assert result["decision"] == "allow"
    assert result["reasons"] == ["ALLOW_HELPER_DRAFT"]


def test_local_acceptance_criteria_draft_lane_is_allowed() -> None:
    result = decision(
        base_task(title="Acceptance criteria draft", draft_only=True, local_lane="acceptance_criteria_draft"),
        3,
    )
    assert result["decision"] == "allow"
    assert result["reasons"] == ["ALLOW_LOCAL_DRAFT_LANE"]


def test_command_center_destructive_action_is_allowed() -> None:
    result = decision(base_task(destructive_action=True), 0)
    assert result["decision"] == "allow"
    assert result["reasons"] == ["ALLOW_COMMAND_CENTER"]


def main() -> int:
    tests = [
        test_helper_cannot_take_final_review,
        test_helper_cannot_take_final_decision,
        test_helper_cannot_take_broad_architecture_ownership,
        test_helper_cannot_take_broad_rewrite,
        test_helper_cannot_take_destructive_operation,
        test_helper_cannot_take_shell_network_or_canonical_mutation,
        test_local_cannot_take_shell_network_or_canonical_mutation,
        test_read_only_review_draft_helper_is_allowed,
        test_local_acceptance_criteria_draft_lane_is_allowed,
        test_command_center_destructive_action_is_allowed,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
