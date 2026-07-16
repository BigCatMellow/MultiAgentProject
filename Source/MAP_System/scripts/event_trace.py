#!/usr/bin/env python3
"""Small helpers for MAP event trace fields.

Trace fields remain optional for legacy compatibility, but new task-scoped
emitters should call these helpers so mission-control can group causal state
without each script inventing its own convention.
"""

from __future__ import annotations

from typing import Any


def trace_id_for_task(task_id: str | None) -> str | None:
    if not task_id:
        return None
    task_id = str(task_id).strip()
    if not task_id:
        return None
    return f"task:{task_id}"


def add_trace_fields(
    event: dict[str, Any],
    *,
    task_id: str | None = None,
    actor: str | None = None,
    action: str | None = None,
    target: str | None = None,
    parent_event_id: str | None = None,
    thread: str | None = None,
) -> dict[str, Any]:
    trace_id = trace_id_for_task(task_id if task_id is not None else event.get("task_id"))
    if trace_id:
        event["trace_id"] = trace_id
    for key, value in {
        "parent_event_id": parent_event_id,
        "actor": actor,
        "action": action,
        "target": target,
        "thread": thread,
    }.items():
        if value is not None and str(value).strip():
            event[key] = str(value)
    return event
