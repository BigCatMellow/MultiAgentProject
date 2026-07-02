#!/usr/bin/env python3
"""Validate and summarize MAP JSONL event logs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVENT_LOG = ROOT / "events" / "events.jsonl"

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
}
TYPE_ALIASES = {
    "REVIEW_APPROVED": "APPROVED",
    "REVIEW_CHANGES_REQUESTED": "CHANGES_REQUESTED",
    "task_progress": "PROGRESS",
}
REQUIRED = {"created_at", "type", "task_id", "sender", "summary"}
OPTIONAL_CANONICAL = {"artifact_paths"}


def validate_event_log(path: Path) -> tuple[list[str], list[str], dict[str, int]]:
    errors: list[str] = []
    warnings: list[str] = []
    counts: dict[str, int] = {}
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {lineno}: invalid JSON: {exc}")
            continue
        if "timestamp" in event and "created_at" not in event:
            warnings.append(f"line {lineno}: legacy timestamp field; use created_at")
            event["created_at"] = event["timestamp"]
        if "agent" in event and "sender" not in event:
            warnings.append(f"line {lineno}: legacy agent field; use sender")
            event["sender"] = event["agent"]
        missing = sorted(REQUIRED - set(event))
        if missing:
            errors.append(f"line {lineno}: missing required field(s): {', '.join(missing)}")
        optional_missing = sorted(OPTIONAL_CANONICAL - set(event))
        if optional_missing:
            warnings.append(f"line {lineno}: missing canonical field(s): {', '.join(optional_missing)}")
        event_type = event.get("type")
        if event_type in TYPE_ALIASES:
            warnings.append(f"line {lineno}: event type {event_type} aliases to {TYPE_ALIASES[event_type]}")
            event_type = TYPE_ALIASES[event_type]
        elif event_type and event_type not in CANONICAL_TYPES:
            warnings.append(f"line {lineno}: non-canonical event type {event_type}")
        if event_type:
            counts[event_type] = counts.get(event_type, 0) + 1
    return errors, warnings, counts


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--event-log", type=Path, default=DEFAULT_EVENT_LOG)
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    errors, warnings, counts = validate_event_log(args.event_log)
    payload = {"errors": errors, "warnings": warnings, "counts": counts}
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        for error in errors:
            print(f"ERROR {error}")
        for warning in warnings:
            print(f"WARN {warning}")
        print(f"SUMMARY errors={len(errors)} warnings={len(warnings)}")
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
