#!/usr/bin/env python3
"""Validate and summarize MAP JSONL event logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENT_LOG = ROOT / "events" / "events.jsonl"
DEFAULT_WARNING_BASELINE = ROOT / "events" / "warning_baseline.json"

CANONICAL_TYPES = {
    "PROGRESS",
    "SUBMISSION",
    "REVIEW_REQUESTED",
    "CHANGES_REQUESTED",
    "APPROVED",
    "RELEASED",
    "QUESTION",
    "ANSWER",
    "BLOCKED",
    "HANDOFF",
    "DECISION_PROPOSED",
    "DECISION_RECORDED",
    "outcome_pass",
    "outcome_fail",
}
TYPE_ALIASES = {
    "REVIEW_APPROVED": "APPROVED",
    "REVIEW_CHANGES_REQUESTED": "CHANGES_REQUESTED",
    "task_progress": "PROGRESS",
}
REQUIRED = {"created_at", "type", "task_id", "sender", "summary"}
OPTIONAL_CANONICAL = {"artifact_paths"}
OUTCOME_TYPES = {"outcome_pass", "outcome_fail"}
OUTCOME_FIELDS = {
    "outcome_id",
    "observed_at",
    "observed_by",
    "outcome_status",
    "use_context",
    "validation_status_at_ship",
    "review_status_at_ship",
    "failure_class",
    "severity",
    "evidence_paths",
    "follow_up",
}
REQUIRED_OUTCOME_FIELDS = {
    "outcome_id",
    "observed_at",
    "observed_by",
    "outcome_status",
    "validation_status_at_ship",
    "review_status_at_ship",
    "follow_up",
}
OUTCOME_STATUSES = {"pass", "fail", "partial", "unknown", "not_exercised"}
VALIDATION_STATUSES = {"passed", "failed", "waived", "not_applicable"}
REVIEW_STATUSES = {"approved", "changes_requested", "waived", "not_applicable"}
FAILURE_CLASSES = {
    "validator_blind_spot",
    "review_blind_spot",
    "requirement_gap",
    "stale_context",
    "integration_gap",
    "operator_mismatch",
    "external_change",
}
SEVERITIES = {"COSMETIC", "DRIFT", "BLOCKING", "STRUCTURAL"}
FOLLOW_UPS = {"none", "repair", "risk", "validator_improvement", "research", "task_backlog"}

# Trace schema (MAP 6.13 Wave 2 / TASK-149): fields for reconstructing a
# causal chain across events, handoffs, and hcom threads. Recognized when
# present, but NOT in OPTIONAL_CANONICAL — they do not warn when absent, so
# existing and near-term event-writing conventions stay unaffected until an
# event append helper exists to populate them by default. Validated for
# shape only when an agent does supply them.
TRACE_FIELDS = {"trace_id", "parent_event_id", "actor", "action", "target", "thread"}


def summary_object(event: dict) -> dict:
    summary = event.get("summary")
    if not isinstance(summary, str):
        return {}
    try:
        parsed = json.loads(summary)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def outcome_payload(event: dict) -> dict:
    """Outcome fields may live at top level or in JSON summary for SQLite compatibility."""
    payload = summary_object(event)
    for field in OUTCOME_FIELDS:
        if field in event:
            payload[field] = event[field]
    return payload


def validate_choice(
    errors: list[str],
    lineno: int,
    payload: dict,
    field: str,
    allowed: set[str],
) -> None:
    value = payload.get(field)
    if value is None:
        return
    if not isinstance(value, str) or value not in allowed:
        errors.append(
            f"line {lineno}: outcome field {field} has invalid value {value!r}; "
            f"expected one of {', '.join(sorted(allowed))}"
        )


def validate_outcome_event(errors: list[str], lineno: int, event: dict) -> None:
    payload = outcome_payload(event)
    missing = sorted(field for field in REQUIRED_OUTCOME_FIELDS if not payload.get(field))
    if missing:
        errors.append(f"line {lineno}: outcome event missing field(s): {', '.join(missing)}")
    validate_choice(errors, lineno, payload, "outcome_status", OUTCOME_STATUSES)
    validate_choice(errors, lineno, payload, "validation_status_at_ship", VALIDATION_STATUSES)
    validate_choice(errors, lineno, payload, "review_status_at_ship", REVIEW_STATUSES)
    validate_choice(errors, lineno, payload, "follow_up", FOLLOW_UPS)
    if payload.get("failure_class"):
        validate_choice(errors, lineno, payload, "failure_class", FAILURE_CLASSES)
    if payload.get("severity"):
        validate_choice(errors, lineno, payload, "severity", SEVERITIES)
    if "evidence_paths" in payload and not isinstance(payload["evidence_paths"], list):
        errors.append(f"line {lineno}: outcome field evidence_paths must be a list")


def load_warning_baseline(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return 0
    return int(data.get("baseline_line_count", 0))


def validate_event_log(
    path: Path, baseline_line_count: int = 0
) -> tuple[list[str], list[str], list[str], dict[str, int]]:
    """Returns (errors, legacy_warnings, new_warnings, type_counts).

    Warnings on lines at or before ``baseline_line_count`` are legacy: known,
    already-accepted noise from before the log's shape was tightened up.
    Warnings past that line are new: a fresh line was appended with a
    warning-worthy shape, which should not be able to hide inside the legacy
    count (see TASK-140 gap #6 / MAP_System/artifacts/reports/task-140-process-use-audit.md).
    """
    errors: list[str] = []
    legacy_warnings: list[str] = []
    new_warnings: list[str] = []
    counts: dict[str, int] = {}

    def warn(lineno: int, message: str) -> None:
        target = legacy_warnings if lineno <= baseline_line_count else new_warnings
        target.append(message)

    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {lineno}: invalid JSON: {exc}")
            continue
        if "timestamp" in event and "created_at" not in event:
            warn(lineno, f"line {lineno}: legacy timestamp field; use created_at")
            event["created_at"] = event["timestamp"]
        if "agent" in event and "sender" not in event:
            warn(lineno, f"line {lineno}: legacy agent field; use sender")
            event["sender"] = event["agent"]
        missing = sorted(REQUIRED - set(event))
        if missing:
            errors.append(f"line {lineno}: missing required field(s): {', '.join(missing)}")
        optional_missing = sorted(OPTIONAL_CANONICAL - set(event))
        if optional_missing:
            warn(lineno, f"line {lineno}: missing canonical field(s): {', '.join(optional_missing)}")
        for field in sorted(TRACE_FIELDS & set(event)):
            value = event[field]
            if not isinstance(value, str) or not value.strip():
                warn(lineno, f"line {lineno}: trace field {field} present but not a non-empty string")
        if "parent_event_id" in event and "trace_id" not in event:
            warn(lineno, f"line {lineno}: parent_event_id present without trace_id")
        event_type = event.get("type")
        if event_type in TYPE_ALIASES:
            warn(lineno, f"line {lineno}: event type {event_type} aliases to {TYPE_ALIASES[event_type]}")
            event_type = TYPE_ALIASES[event_type]
        elif event_type and event_type not in CANONICAL_TYPES:
            warn(lineno, f"line {lineno}: non-canonical event type {event_type}")
        if event_type in OUTCOME_TYPES:
            validate_outcome_event(errors, lineno, event)
        if event_type:
            counts[event_type] = counts.get(event_type, 0) + 1
    return errors, legacy_warnings, new_warnings, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-log", type=Path, default=DEFAULT_EVENT_LOG)
    parser.add_argument(
        "--warning-baseline",
        type=Path,
        default=DEFAULT_WARNING_BASELINE,
        help="JSON file with a baseline_line_count marking known legacy-warning lines",
    )
    parser.add_argument("--strict", action="store_true", help="Treat any warning (legacy or new) as a failure")
    parser.add_argument(
        "--fail-on-new",
        action="store_true",
        help="Treat only warnings past the baseline line count as failures; legacy warnings stay non-blocking",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    baseline_line_count = load_warning_baseline(args.warning_baseline)
    errors, legacy_warnings, new_warnings, counts = validate_event_log(
        args.event_log, baseline_line_count
    )
    warnings = legacy_warnings + new_warnings
    payload = {
        "errors": errors,
        "legacy_warnings": legacy_warnings,
        "new_warnings": new_warnings,
        "baseline_line_count": baseline_line_count,
        "counts": counts,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for error in errors:
            print(f"ERROR {error}")
        for warning in legacy_warnings:
            print(f"WARN {warning}")
        for warning in new_warnings:
            print(f"WARN-NEW {warning}")
        print(
            f"SUMMARY errors={len(errors)} legacy_warnings={len(legacy_warnings)} "
            f"new_warnings={len(new_warnings)} baseline_line_count={baseline_line_count}"
        )
    if errors or (args.strict and warnings) or (args.fail_on_new and new_warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
