#!/usr/bin/env python3
"""Tests for MAP cost governance helpers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.cost_governance import (  # noqa: E402
    CostGovernanceError,
    load_cost_state,
    record_cost_event,
    validate_cost_fields,
)
from MAP_System.scripts.halt_state import load_halt_state  # noqa: E402


def test_cost_counter_records_known_paid_cost() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "cost.json"
        halt_path = Path(tmp) / "halt.json"
        result = record_cost_event(
            {
                "model_tier": "standard",
                "cost_source": "static_rate",
                "estimated_cost": 1.25,
                "tokens_in": 100,
                "tokens_out": 50,
            },
            state_path=state_path,
            halt_path=halt_path,
            budget_scope="task",
            budget_key="TASK-159",
            budget_limit=5.0,
        )

        state = load_cost_state(state_path)
        assert result["status"] == "recorded"
        assert state["counters"]["task:TASK-159"]["spent"] == 1.25
        assert load_halt_state(halt_path)["state"] == "clear"


def test_paid_unknown_cost_sets_paid_dispatch_halt_not_zero_cost() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "cost.json"
        halt_path = Path(tmp) / "halt.json"
        result = record_cost_event(
            {
                "model_tier": "premium",
                "cost_source": "unknown",
                "estimated_cost": None,
            },
            state_path=state_path,
            halt_path=halt_path,
            budget_scope="daily",
            budget_key="TEST",
        )

        state = load_cost_state(state_path)
        halt = load_halt_state(halt_path)
        assert result["status"] == "halted_unknown_cost"
        assert state["counters"][result["counter_key"]]["spent"] == 0.0
        assert halt["state"] == "halt_paid_dispatch"
        assert halt["reason"] == "unknown_cost_paid_dispatch"


def test_local_missing_cost_records_as_zero_only_for_local_lane() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "cost.json"
        halt_path = Path(tmp) / "halt.json"
        result = record_cost_event(
            {
                "model_tier": "local",
                "cost_source": "local_zero",
                "estimated_cost": None,
            },
            state_path=state_path,
            halt_path=halt_path,
            budget_scope="system",
            budget_key="local",
        )

        state = load_cost_state(state_path)
        assert result["status"] == "recorded"
        assert state["counters"]["system:local"]["spent"] == 0.0
        assert load_halt_state(halt_path)["state"] == "clear"


def test_budget_limit_breach_sets_spend_rate_halt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        state_path = Path(tmp) / "cost.json"
        halt_path = Path(tmp) / "halt.json"
        result = record_cost_event(
            {
                "model_tier": "low",
                "cost_source": "static_rate",
                "estimated_cost": 3.0,
            },
            state_path=state_path,
            halt_path=halt_path,
            budget_scope="task",
            budget_key="TASK-X",
            budget_limit=2.0,
        )

        halt = load_halt_state(halt_path)
        assert result["status"] == "halted_budget_exceeded"
        assert halt["state"] == "halt_paid_dispatch"
        assert halt["reason"] == "spend_rate_breaker"


def test_negative_cost_fields_are_invalid() -> None:
    errors = validate_cost_fields({"tokens_in": -1, "estimated_cost": -0.01})
    assert "tokens_in must be an integer >= 0" in errors
    assert "estimated_cost must be >= 0" in errors

    try:
        record_cost_event({"model_tier": "standard", "cost_source": "static_rate", "estimated_cost": -1})
    except CostGovernanceError as exc:
        assert "estimated_cost must be >= 0" in str(exc)
    else:  # pragma: no cover - defensive failure path
        raise AssertionError("negative cost was accepted")


def main() -> int:
    tests = [
        test_cost_counter_records_known_paid_cost,
        test_paid_unknown_cost_sets_paid_dispatch_halt_not_zero_cost,
        test_local_missing_cost_records_as_zero_only_for_local_lane,
        test_budget_limit_breach_sets_spend_rate_halt,
        test_negative_cost_fields_are_invalid,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
