#!/usr/bin/env python3
"""MAP cost accounting and spend-breaker helpers."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any

try:
    from MAP_System.scripts.halt_state import set_halt
except ModuleNotFoundError:  # pragma: no cover - script execution from MAP_System
    from halt_state import set_halt  # type: ignore


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COST_STATE_PATH = ROOT / "shared" / "cost-governance-state.json"

PAID_MODEL_TIERS = {"low", "standard", "premium", "unknown"}
FREE_MODEL_TIERS = {"local", "manual", "no_cost", "none"}


class CostGovernanceError(ValueError):
    """Raised for invalid cost records or budget transitions."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def empty_cost_state() -> dict[str, Any]:
    return {"version": 1, "counters": {}, "events": []}


def load_cost_state(path: str | Path = DEFAULT_COST_STATE_PATH) -> dict[str, Any]:
    cost_path = Path(path)
    if not cost_path.exists():
        return empty_cost_state()
    state = json.loads(cost_path.read_text(encoding="utf-8"))
    if not isinstance(state.get("counters"), dict):
        raise CostGovernanceError("cost state counters must be a mapping")
    if not isinstance(state.get("events"), list):
        raise CostGovernanceError("cost state events must be a list")
    return state


def write_cost_state(state: dict[str, Any], path: str | Path = DEFAULT_COST_STATE_PATH) -> dict[str, Any]:
    cost_path = Path(path)
    cost_path.parent.mkdir(parents=True, exist_ok=True)
    cost_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return state


def is_paid_model_tier(model_tier: str | None) -> bool:
    tier = (model_tier or "unknown").lower()
    return tier not in FREE_MODEL_TIERS


def validate_cost_fields(event: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("tokens_in", "tokens_out"):
        if field in event and (not isinstance(event[field], int) or event[field] < 0):
            errors.append(f"{field} must be an integer >= 0")
    if "estimated_cost" in event and event["estimated_cost"] is not None:
        try:
            cost = float(event["estimated_cost"])
        except (TypeError, ValueError):
            errors.append("estimated_cost must be numeric when present")
        else:
            if cost < 0:
                errors.append("estimated_cost must be >= 0")
    return errors


def paid_cost_is_unknown(event: dict[str, Any]) -> bool:
    if not is_paid_model_tier(event.get("model_tier")):
        return False
    return event.get("estimated_cost") is None or event.get("cost_source") in {None, "", "unknown"}


def normalized_cost(event: dict[str, Any]) -> float:
    errors = validate_cost_fields(event)
    if errors:
        raise CostGovernanceError("; ".join(errors))
    if paid_cost_is_unknown(event):
        raise CostGovernanceError("paid dispatch cost is unknown")
    if event.get("estimated_cost") is None:
        if is_paid_model_tier(event.get("model_tier")):
            raise CostGovernanceError("paid dispatch cost is unknown")
        return 0.0
    return float(event["estimated_cost"])


def counter_key(scope: str, key: str | None, now: datetime | None = None) -> str:
    if scope == "daily":
        day = (now or datetime.now(timezone.utc)).date().isoformat()
        return f"daily:{key or 'system'}:{day}"
    if scope in {"task", "project", "agent", "system"}:
        return f"{scope}:{key or 'default'}"
    raise CostGovernanceError(f"invalid budget scope: {scope}")


def record_cost_event(
    event: dict[str, Any],
    *,
    state_path: str | Path = DEFAULT_COST_STATE_PATH,
    halt_path: str | Path | None = None,
    budget_scope: str = "daily",
    budget_key: str | None = None,
    budget_limit: float | None = None,
    set_by: str = "cost-governance",
) -> dict[str, Any]:
    """Record cost and set paid-dispatch halt when paid spend is unsafe."""
    errors = validate_cost_fields(event)
    if errors:
        raise CostGovernanceError("; ".join(errors))

    state = load_cost_state(state_path)
    key = counter_key(budget_scope, budget_key)
    counter = state["counters"].setdefault(
        key,
        {"scope": budget_scope, "key": budget_key, "spent": 0.0, "limit": budget_limit, "events": 0},
    )
    if budget_limit is not None:
        counter["limit"] = budget_limit

    if paid_cost_is_unknown(event):
        halt = set_halt(
            state="halt_paid_dispatch",
            reason="unknown_cost_paid_dispatch",
            set_by=set_by,
            scope="paid",
            clear_requires="objective_cost_source",
            path=halt_path,
        )
        payload = {
            "status": "halted_unknown_cost",
            "counter_key": key,
            "spent": counter["spent"],
            "halt_id": halt["halt_id"],
        }
        state["events"].append({"recorded_at": utc_now(), **event, **payload})
        write_cost_state(state, state_path)
        return payload

    amount = normalized_cost(event)
    counter["spent"] = round(float(counter.get("spent", 0.0)) + amount, 6)
    counter["events"] = int(counter.get("events", 0)) + 1

    payload = {"status": "recorded", "counter_key": key, "spent": counter["spent"]}
    limit = counter.get("limit")
    if limit is not None and counter["spent"] > float(limit):
        halt = set_halt(
            state="halt_paid_dispatch",
            reason="spend_rate_breaker",
            set_by=set_by,
            scope="paid",
            clear_requires="command_center",
            path=halt_path,
        )
        payload.update({"status": "halted_budget_exceeded", "halt_id": halt["halt_id"]})

    state["events"].append({"recorded_at": utc_now(), **event, **payload})
    write_cost_state(state, state_path)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-path", type=Path, default=DEFAULT_COST_STATE_PATH)
    parser.add_argument("--halt-path", type=Path)
    parser.add_argument("--budget-scope", default="daily")
    parser.add_argument("--budget-key")
    parser.add_argument("--budget-limit", type=float)
    parser.add_argument("--model-tier", default="unknown")
    parser.add_argument("--cost-source", default="unknown")
    parser.add_argument("--estimated-cost", type=float)
    parser.add_argument("--tokens-in", type=int)
    parser.add_argument("--tokens-out", type=int)
    args = parser.parse_args()

    event = {
        "model_tier": args.model_tier,
        "cost_source": args.cost_source,
        "estimated_cost": args.estimated_cost,
        "tokens_in": args.tokens_in,
        "tokens_out": args.tokens_out,
    }
    payload = record_cost_event(
        event,
        state_path=args.state_path,
        halt_path=args.halt_path,
        budget_scope=args.budget_scope,
        budget_key=args.budget_key,
        budget_limit=args.budget_limit,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
