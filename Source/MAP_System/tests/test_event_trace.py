#!/usr/bin/env python3
"""Tests for MAP event trace helper conventions."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.event_trace import add_trace_fields, trace_id_for_task  # noqa: E402


def test_trace_id_for_task_uses_stable_task_prefix() -> None:
    assert trace_id_for_task("TASK-170") == "task:TASK-170"
    assert trace_id_for_task(" TASK-170 ") == "task:TASK-170"


def test_trace_id_for_task_skips_missing_or_blank_task() -> None:
    assert trace_id_for_task(None) is None
    assert trace_id_for_task("") is None
    assert trace_id_for_task("   ") is None


def test_add_trace_fields_uses_event_task_id_by_default() -> None:
    event = {"task_id": "TASK-170", "type": "PROGRESS"}
    returned = add_trace_fields(event, actor="codex-lab-mozu", action="progress", target="TASK-170")

    assert returned is event
    assert event["trace_id"] == "task:TASK-170"
    assert event["actor"] == "codex-lab-mozu"
    assert event["action"] == "progress"
    assert event["target"] == "TASK-170"


def test_add_trace_fields_allows_explicit_task_id_and_optional_links() -> None:
    event = {"task_id": "TASK-OLD", "type": "PROGRESS"}
    add_trace_fields(
        event,
        task_id="TASK-NEW",
        parent_event_id="evt-1",
        thread="map-613",
    )

    assert event["trace_id"] == "task:TASK-NEW"
    assert event["parent_event_id"] == "evt-1"
    assert event["thread"] == "map-613"


def test_add_trace_fields_omits_blank_optional_values() -> None:
    event = {"task_id": "TASK-170", "type": "PROGRESS"}
    add_trace_fields(event, actor=" ", action="", target=None, thread=" ")

    assert event == {
        "task_id": "TASK-170",
        "type": "PROGRESS",
        "trace_id": "task:TASK-170",
    }


def main() -> int:
    tests = [
        test_trace_id_for_task_uses_stable_task_prefix,
        test_trace_id_for_task_skips_missing_or_blank_task,
        test_add_trace_fields_uses_event_task_id_by_default,
        test_add_trace_fields_allows_explicit_task_id_and_optional_links,
        test_add_trace_fields_omits_blank_optional_values,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
