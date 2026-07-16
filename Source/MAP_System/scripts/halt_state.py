#!/usr/bin/env python3
"""Durable MAP dispatch halt state helpers.

The halt store is intentionally small JSON so command-center can inspect and
edit around it with ordinary file tools if recovery requires it.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HALT_PATH = ROOT / "shared" / "halt-state.json"
DEFAULT_RUNTIME_POLICY_PATH = ROOT / "workflow" / "runtime_policy.yaml"
DEFAULT_EVENT_LOG = ROOT / "events" / "events.jsonl"

VALID_STATES = {"clear", "halt_paid_dispatch", "halt_all_dispatch", "repair_only"}
VALID_SCOPES = {"paid", "project", "task", "agent", "global"}
VALID_HALT_AUTHORITY_SCOPES = {"layer1", "protocol", "*"}
REQUIRED_FIELDS = {
    "halt_id",
    "state",
    "reason",
    "set_by",
    "set_at",
    "scope",
    "target",
    "clear_requires",
    "cleared_by",
    "cleared_at",
    "clear_reason",
    "related_event_ids",
}

COMMAND_CENTER_IDENTITIES = {"command-center", "bigboss", "operator"}
SYSTEM_SETTERS = {"cost-governance", "validator", "validate_layer1", "langgraph-runner"}
CORE_AGENT_PREFIXES = (
    "codex",
    "claude",
    "gemini",
    "opencode",
    "antigravity",
    "kilo",
    "pi",
    "agy",
    "cursor",
    "kimi",
    "copilot",
)
HELPER_PREFIXES = ("task", "helper", "review")


class HaltStateError(ValueError):
    """Raised when a halt transition is malformed or unauthorized."""


def current_halt_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    return Path(os.environ.get("MAP_HALT_STATE_PATH", DEFAULT_HALT_PATH))


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _parse_iso_datetime(value: str) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_window_scopes(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        scopes = [value]
    elif isinstance(value, list):
        scopes = [str(item) for item in value]
    else:
        scopes = []
    return [scope.strip().lower() for scope in scopes if scope and scope.strip()]


def _json_safe_window_value(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    return value


def load_runtime_policy(path: str | Path | None = None) -> dict[str, Any]:
    policy_path = Path(path) if path is not None else DEFAULT_RUNTIME_POLICY_PATH
    if not policy_path.exists():
        return {}
    data = yaml.safe_load(policy_path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        return {}
    runtime_policy = data.get("runtime_policy", data)
    return runtime_policy if isinstance(runtime_policy, dict) else {}


def halt_authority_window_status(
    validator_scope: str,
    *,
    runtime_policy_path: str | Path | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Return whether the passive validator halt-authority window is active.

    The fail-safe default is inactive: missing config, null timestamps, past
    timestamps, invalid timestamps, or scope mismatch all preserve the existing
    telemetry-only validator behavior.
    """
    policy = load_runtime_policy(runtime_policy_path)
    window = policy.get("halt_authority_window") or {}
    if not isinstance(window, dict):
        window = {}

    enabled_until = window.get("enabled_until")
    scopes = _normalize_window_scopes(window.get("scope"))
    granted_by = window.get("granted_by")
    scope = validator_scope.strip().lower()
    current = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)

    base = {
        "active": False,
        "validator_scope": scope,
        "enabled_until": _json_safe_window_value(enabled_until),
        "granted_by": granted_by,
        "scopes": scopes,
        "adjudication": "pending",
    }
    if not enabled_until:
        return {**base, "reason": "disabled"}
    try:
        expires_at = _parse_iso_datetime(str(enabled_until))
    except ValueError:
        return {**base, "reason": "invalid_enabled_until"}
    if current >= expires_at:
        return {**base, "reason": "expired"}
    if scope not in VALID_HALT_AUTHORITY_SCOPES:
        return {**base, "reason": "unknown_validator_scope"}
    if "*" not in scopes and scope not in scopes:
        return {**base, "reason": "scope_mismatch"}
    return {**base, "active": True, "reason": "active"}


def append_validator_halt_event(
    *,
    event_log_path: str | Path,
    task_id: str,
    sender: str,
    validator_scope: str,
    decision: str,
    window_status: dict[str, Any],
    configured_severity: str,
    effective_severity: str,
    halt_id: str | None = None,
    reasons: list[str] | None = None,
) -> None:
    event_log = Path(event_log_path)
    event_log.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "kind": "validator_halt_authority",
        "validator_scope": validator_scope,
        "decision": decision,
        "window_active": bool(window_status.get("active")),
        "window_reason": window_status.get("reason"),
        "enabled_until": window_status.get("enabled_until"),
        "granted_by": window_status.get("granted_by"),
        "window_scopes": window_status.get("scopes", []),
        "configured_severity": configured_severity,
        "effective_severity": effective_severity,
        "halt_id": halt_id,
        "reasons": reasons or [],
        "adjudication": "pending",
    }
    payload = {
        "created_at": utc_now(),
        "type": "PROGRESS",
        "task_id": task_id,
        "sender": sender,
        "summary": json.dumps(summary, sort_keys=True),
        "artifact_paths": [],
    }
    with event_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")


def clear_record() -> dict[str, Any]:
    return {
        "halt_id": None,
        "state": "clear",
        "reason": "none",
        "set_by": None,
        "set_at": None,
        "scope": "global",
        "target": None,
        "clear_requires": "none",
        "cleared_by": None,
        "cleared_at": None,
        "clear_reason": "",
        "related_event_ids": [],
    }


def is_command_center(identity: str | None) -> bool:
    return (identity or "").lower() in COMMAND_CENTER_IDENTITIES


def is_helper_identity(identity: str | None) -> bool:
    normalized = (identity or "").lower()
    return normalized.startswith(HELPER_PREFIXES) or "helper" in normalized or "review-" in normalized


def is_core_agent(identity: str | None) -> bool:
    normalized = (identity or "").lower()
    if not normalized or is_helper_identity(normalized):
        return False
    return normalized.startswith(CORE_AGENT_PREFIXES) or "-lab-" in normalized


def can_set_halt(identity: str | None, state: str, reason: str) -> bool:
    normalized = (identity or "").lower()
    if is_command_center(normalized):
        return True
    if state == "halt_paid_dispatch":
        return is_core_agent(normalized) or normalized in SYSTEM_SETTERS
    if state == "halt_all_dispatch":
        return normalized.startswith("validator") and reason == "validator_blocking_anomaly"
    if state == "repair_only":
        return is_core_agent(normalized) or normalized.startswith("validator")
    return False


def can_clear_halt(identity: str | None, record: dict[str, Any]) -> bool:
    normalized = (identity or "").lower()
    if is_helper_identity(normalized):
        return False
    if is_command_center(normalized):
        return True
    if record.get("scope") == "global":
        return False
    state = record.get("state")
    reason = record.get("reason")
    scope = record.get("scope")
    if state == "halt_paid_dispatch" and scope == "paid":
        return is_core_agent(normalized) and record.get("clear_requires") != "command_center"
    if reason == "validator_blocking_anomaly":
        return normalized.startswith("validator")
    return False


def validate_halt_record(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(REQUIRED_FIELDS - set(record))
    if missing:
        errors.append(f"missing fields: {', '.join(missing)}")
        return errors

    state = record.get("state")
    if state not in VALID_STATES:
        errors.append(f"invalid state: {state}")
    scope = record.get("scope")
    if scope not in VALID_SCOPES:
        errors.append(f"invalid scope: {scope}")
    related = record.get("related_event_ids")
    if not isinstance(related, list):
        errors.append("related_event_ids must be a list")

    if state != "clear":
        for field in ("halt_id", "reason", "set_by", "set_at", "clear_requires"):
            if not record.get(field):
                errors.append(f"{field} is required for active halt")
    else:
        if record.get("cleared_by") and not record.get("cleared_at"):
            errors.append("cleared_at is required when cleared_by is set")

    return errors


def load_halt_state(path: str | Path | None = None) -> dict[str, Any]:
    halt_path = current_halt_path(path)
    if not halt_path.exists():
        return clear_record()
    record = json.loads(halt_path.read_text(encoding="utf-8"))
    errors = validate_halt_record(record)
    if errors:
        raise HaltStateError("; ".join(errors))
    return record


def write_halt_state(record: dict[str, Any], path: str | Path | None = None) -> dict[str, Any]:
    errors = validate_halt_record(record)
    if errors:
        raise HaltStateError("; ".join(errors))
    halt_path = current_halt_path(path)
    halt_path.parent.mkdir(parents=True, exist_ok=True)
    halt_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return record


def set_halt(
    *,
    state: str,
    reason: str,
    set_by: str,
    scope: str = "global",
    target: str | None = None,
    clear_requires: str = "command_center",
    related_event_ids: list[str] | None = None,
    path: str | Path | None = None,
) -> dict[str, Any]:
    if state == "clear":
        raise HaltStateError("use clear_halt() to clear halt state")
    if state not in VALID_STATES:
        raise HaltStateError(f"invalid state: {state}")
    if scope not in VALID_SCOPES:
        raise HaltStateError(f"invalid scope: {scope}")
    if not can_set_halt(set_by, state, reason):
        raise HaltStateError(f"{set_by} is not authorized to set {state}")

    record = {
        "halt_id": f"HALT-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}",
        "state": state,
        "reason": reason,
        "set_by": set_by,
        "set_at": utc_now(),
        "scope": scope,
        "target": target,
        "clear_requires": clear_requires,
        "cleared_by": None,
        "cleared_at": None,
        "clear_reason": "",
        "related_event_ids": related_event_ids or [],
    }
    return write_halt_state(record, path)


def clear_halt(
    *,
    cleared_by: str,
    clear_reason: str,
    related_event_ids: list[str] | None = None,
    path: str | Path | None = None,
) -> dict[str, Any]:
    record = load_halt_state(path)
    if record.get("state") == "clear":
        return record
    if not clear_reason.strip():
        raise HaltStateError("clear_reason is required")
    if not can_clear_halt(cleared_by, record):
        raise HaltStateError(f"{cleared_by} is not authorized to clear {record.get('state')}")

    cleared = {
        **record,
        "state": "clear",
        "cleared_by": cleared_by,
        "cleared_at": utc_now(),
        "clear_reason": clear_reason,
        "related_event_ids": [*record.get("related_event_ids", []), *(related_event_ids or [])],
    }
    return write_halt_state(cleared, path)


def classify_task_lane(task: dict[str, Any]) -> str:
    task_type = str(task.get("task_type", "")).lower()
    role = str(task.get("role", "")).lower()
    model_tier = str(task.get("model_tier", "") or task.get("budget_model_tier", "")).lower()
    text = " ".join(
        str(value).lower()
        for value in (task.get("title", ""), task.get("description", ""))
    )

    if task_type == "review" or role == "reviewer":
        return "review"
    if "repair" in {task_type, role} or task_type == "self_repair" or "repair" in text:
        return "repair"
    if task_type in {"operator_decision", "decision", "authority"} or role in {"operator", "decision_owner"}:
        return "operator"
    if task_type in {"inspection", "read_only"} or role in {"inspector", "observer"}:
        return "read_only"
    if model_tier in {"local", "manual", "no_cost"} or task_type in {"local", "no_cost"}:
        return "local"
    return "paid"


def allowed_lanes(record: dict[str, Any]) -> set[str]:
    state = record.get("state")
    if state == "clear":
        return {"paid", "review", "repair", "operator", "read_only", "local"}
    if state == "halt_paid_dispatch":
        return {"review", "repair", "operator", "read_only", "local"}
    if state == "halt_all_dispatch":
        return {"review", "repair", "operator", "read_only"}
    if state == "repair_only":
        return {"repair", "operator"}
    return set()


def dispatch_block_reason_for_task(
    task: dict[str, Any],
    record: dict[str, Any] | None = None,
    *,
    path: str | Path | None = None,
) -> str | None:
    halt = record if record is not None else load_halt_state(path)
    if halt.get("state") == "clear":
        return None
    lane = classify_task_lane(task)
    if lane in allowed_lanes(halt):
        return None
    scope = halt.get("scope")
    target = halt.get("target")
    if scope == "task" and target and target != task.get("task_id"):
        return None
    if scope == "project" and target and target != task.get("project_id"):
        return None
    return str(halt.get("state"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("show")
    show.add_argument("--path", type=Path)

    set_cmd = sub.add_parser("set")
    set_cmd.add_argument("state", choices=sorted(VALID_STATES - {"clear"}))
    set_cmd.add_argument("--reason", required=True)
    set_cmd.add_argument("--set-by", required=True)
    set_cmd.add_argument("--scope", choices=sorted(VALID_SCOPES), default="global")
    set_cmd.add_argument("--target")
    set_cmd.add_argument("--clear-requires", default="command_center")
    set_cmd.add_argument("--path", type=Path)

    clear_cmd = sub.add_parser("clear")
    clear_cmd.add_argument("--cleared-by", required=True)
    clear_cmd.add_argument("--clear-reason", required=True)
    clear_cmd.add_argument("--path", type=Path)

    args = parser.parse_args()
    if args.command == "show":
        record = load_halt_state(args.path)
    elif args.command == "set":
        record = set_halt(
            state=args.state,
            reason=args.reason,
            set_by=args.set_by,
            scope=args.scope,
            target=args.target,
            clear_requires=args.clear_requires,
            path=args.path,
        )
    else:
        record = clear_halt(cleared_by=args.cleared_by, clear_reason=args.clear_reason, path=args.path)
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
