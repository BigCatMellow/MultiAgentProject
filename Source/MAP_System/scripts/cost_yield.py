#!/usr/bin/env python3
"""Per-task cost-proxy x outcome rollup (TASK-190, codeburn yield.ts pattern).

Answers, from existing MAP data only: "what did this task cost, and did it
produce released work?" Joins per-task event volume from events/events.jsonl
with lifecycle state from map.db, classifies each task's outcome, and splits
proxy spend productive-vs-abandoned.

All cost signals are PROXIES -- event volume, wall-clock activity span,
attempts, rework rounds. No dollar figures are computed or implied; MAP has
no per-task token or currency data.

Read-only against canonical state: the DB is opened mode=ro and nothing is
written anywhere.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "map.db"
DEFAULT_EVENTS = ROOT / "events" / "events.jsonl"

# Same normalization as map_metrics.py so both reports agree on event types.
EVENT_ALIASES = {
    "REVIEW_APPROVED": "APPROVED",
    "REVIEW_CHANGES_REQUESTED": "CHANGES_REQUESTED",
    "task_progress": "PROGRESS",
}

# Outcome classes (codeburn yield.ts vocabulary adapted to MAP's status
# taxonomy). DONE is kept out of "abandoned": the DONE rows are legacy
# pre-release-gate bootstrap completions (all imported 2026-07-02, before the
# first task_release_records row), so counting them as abandoned spend would
# misstate the split.
OUTCOME_BY_STATUS = {
    "RELEASED": "released",
    "APPROVED": "approved_not_released",
    "RETIRED": "retired",
    "DONE": "legacy_done",
}
TERMINAL_STATUSES = {"RELEASED", "APPROVED", "RETIRED", "DONE", "FAILED", "CANCELLED"}
OUTCOME_ORDER = ["released", "approved_not_released", "retired",
                 "abandoned", "legacy_done", "in_flight"]

# Spend-split buckets over outcome classes (productive/abandoned mirrors
# codeburn's productive/reverted+abandoned; pending is work still in the
# pipeline, legacy is pre-gate history).
SPLIT_BUCKETS = {
    "productive": ["released"],
    "abandoned": ["retired", "abandoned"],
    "pending": ["approved_not_released", "in_flight"],
    "legacy": ["legacy_done"],
}

PROXY_NOTE = ("Cost signals are PROXIES (event volume, wall-clock activity span, "
              "attempts, rework rounds) -- not dollars. No currency data exists "
              "per task and none is fabricated here.")


def classify_outcome(status: str | None) -> str:
    """Task status -> outcome class. Unknown terminal statuses count as
    abandoned (terminal-but-unreleased); anything non-terminal is in flight."""
    if status in OUTCOME_BY_STATUS:
        return OUTCOME_BY_STATUS[status]
    if status in TERMINAL_STATUSES:
        return "abandoned"
    return "in_flight"


def parse_ts(value: Any) -> datetime | None:
    """ISO-8601 string -> aware datetime, or None. Mixed offsets ('Z' and
    numeric) both occur in events.jsonl; naive values are never guessed at
    beyond fromisoformat's own parse."""
    if not value or not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed


def load_events(path: Path) -> list[dict[str, Any]]:
    events = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                events.append(event)
    return events


def aggregate_events(events: list[dict[str, Any]]) -> dict[str | None, dict[str, Any]]:
    """Per-task event aggregates keyed by task_id (None collects events with
    no task attribution). Event types are alias-normalized."""
    per_task: dict[str | None, dict[str, Any]] = {}
    for event in events:
        task_id = event.get("task_id")
        agg = per_task.setdefault(task_id, {
            "events_total": 0, "event_counts": {},
            "first_event_at": None, "last_event_at": None,
            "submitted_at": None, "approved_at": None, "released_at": None,
        })
        event_type = EVENT_ALIASES.get(event.get("type"), event.get("type"))
        agg["events_total"] += 1
        agg["event_counts"][event_type] = agg["event_counts"].get(event_type, 0) + 1
        ts = parse_ts(event.get("created_at"))
        if ts is None:
            continue
        if agg["first_event_at"] is None or ts < agg["first_event_at"]:
            agg["first_event_at"] = ts
        if agg["last_event_at"] is None or ts > agg["last_event_at"]:
            agg["last_event_at"] = ts
        marker = {"SUBMISSION": "submitted_at", "APPROVED": "approved_at",
                  "RELEASED": "released_at"}.get(event_type)
        if marker and (agg[marker] is None or ts < agg[marker]):
            agg[marker] = ts
    return per_task


def load_tasks(db_path: Path) -> list[dict[str, Any]]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        "SELECT task_id, title, status, owner, attempt, created_at "
        "FROM tasks ORDER BY task_id").fetchall()
    con.close()
    return [dict(row) for row in rows]


def span_hours(first: datetime | None, last: datetime | None) -> float:
    if first is None or last is None:
        return 0.0
    return round((last - first).total_seconds() / 3600, 2)


def percent(part: float, whole: float) -> float:
    return round(part / whole * 1000) / 10 if whole else 0.0


def build_rollup(tasks: list[dict[str, Any]],
                 per_task_events: dict[str | None, dict[str, Any]]) -> dict[str, Any]:
    """Pure join: DB task rows x event aggregates -> rollup structure."""
    known_ids = {t["task_id"] for t in tasks}
    details = []
    for task in tasks:
        agg = per_task_events.get(task["task_id"], {})
        counts = agg.get("event_counts", {})
        iso = lambda ts: ts.isoformat(timespec="seconds") if ts else None
        details.append({
            "task_id": task["task_id"],
            "title": task["title"],
            "status": task["status"],
            "outcome": classify_outcome(task["status"]),
            "attempts": task["attempt"],
            "events_total": agg.get("events_total", 0),
            "event_counts": dict(sorted(counts.items())),
            "rework_rounds": counts.get("CHANGES_REQUESTED", 0),
            "span_hours": span_hours(agg.get("first_event_at"), agg.get("last_event_at")),
            "lifecycle": {
                "created_at": task["created_at"],
                "first_event_at": iso(agg.get("first_event_at")),
                "submitted_at": iso(agg.get("submitted_at")),
                "approved_at": iso(agg.get("approved_at")),
                "released_at": iso(agg.get("released_at")),
                "last_event_at": iso(agg.get("last_event_at")),
            },
        })

    classes: dict[str, dict[str, Any]] = {}
    for outcome in OUTCOME_ORDER:
        rows = [d for d in details if d["outcome"] == outcome]
        statuses: dict[str, int] = {}
        for row in rows:
            statuses[row["status"]] = statuses.get(row["status"], 0) + 1
        classes[outcome] = {
            "tasks": len(rows),
            "events": sum(d["events_total"] for d in rows),
            "span_hours": round(sum(d["span_hours"] for d in rows), 2),
            "attempts": sum(d["attempts"] for d in rows),
            "rework_rounds": sum(d["rework_rounds"] for d in rows),
            "statuses": dict(sorted(statuses.items())),
        }

    total_events_attributed = sum(c["events"] for c in classes.values())
    for cls in classes.values():
        cls["event_percent"] = percent(cls["events"], total_events_attributed)

    split = {}
    for bucket, outcomes in SPLIT_BUCKETS.items():
        split[bucket] = {
            "outcomes": outcomes,
            "tasks": sum(classes[o]["tasks"] for o in outcomes),
            "events": sum(classes[o]["events"] for o in outcomes),
            "span_hours": round(sum(classes[o]["span_hours"] for o in outcomes), 2),
            "event_percent": percent(sum(classes[o]["events"] for o in outcomes),
                                     total_events_attributed),
        }
    abandoned_events = split["abandoned"]["events"]
    split["productive_to_abandoned_event_ratio"] = (
        round(split["productive"]["events"] / abandoned_events, 2)
        if abandoned_events else None)

    released = [d for d in details if d["outcome"] == "released"]
    n_released = len(released)
    avg = lambda vals: round(sum(vals) / n_released, 2) if n_released else None
    cost_by_released = {
        "released_tasks": n_released,
        "events_per_released_task_avg": avg([d["events_total"] for d in released]),
        "span_hours_per_released_task_avg": avg([d["span_hours"] for d in released]),
        "attempts_per_released_task_avg": avg([d["attempts"] for d in released]),
        "rework_rounds_per_released_task_avg": avg([d["rework_rounds"] for d in released]),
        # all-in view: every attributed event (including abandoned/pending
        # spend) divided by released outputs -- the true proxy price of one
        # released task at current yield
        "all_in_events_per_release": (round(total_events_attributed / n_released, 2)
                                      if n_released else None),
    }

    unattributed = per_task_events.get(None, {}).get("events_total", 0)
    unknown_ids = sorted(tid for tid in per_task_events
                         if tid is not None and tid not in known_ids)
    return {
        "proxy_note": PROXY_NOTE,
        "totals": {
            "tasks": len(details),
            "events_attributed": total_events_attributed,
            "events_unattributed": unattributed,
            "events_unknown_task": sum(per_task_events[t]["events_total"]
                                       for t in unknown_ids),
        },
        "outcome_classes": classes,
        "spend_split": split,
        "cost_by_released_output": cost_by_released,
        "unknown_task_ids": unknown_ids,
        "tasks": details,
    }


def print_table(rollup: dict[str, Any], limit: int) -> None:
    print("MAP Cost/Yield Rollup")
    print()
    print(f"Note: {rollup['proxy_note']}")
    print()
    totals = rollup["totals"]
    print(f"Tasks: {totals['tasks']}  |  events attributed: "
          f"{totals['events_attributed']}  |  unattributed: "
          f"{totals['events_unattributed']}  |  unknown-task: "
          f"{totals['events_unknown_task']}")
    print()
    print("Outcome classes (proxy spend)")
    print("| Outcome | Tasks | Events | Event % | Span h | Attempts | Rework |")
    print("|---|---:|---:|---:|---:|---:|---:|")
    for outcome in OUTCOME_ORDER:
        cls = rollup["outcome_classes"][outcome]
        print(f"| {outcome} | {cls['tasks']} | {cls['events']} | "
              f"{cls['event_percent']}% | {cls['span_hours']} | "
              f"{cls['attempts']} | {cls['rework_rounds']} |")
    print()
    print("Productive vs abandoned split (by attributed events)")
    print("| Bucket | Tasks | Events | Event % | Span h |")
    print("|---|---:|---:|---:|---:|")
    for bucket in SPLIT_BUCKETS:
        row = rollup["spend_split"][bucket]
        print(f"| {bucket} | {row['tasks']} | {row['events']} | "
              f"{row['event_percent']}% | {row['span_hours']} |")
    ratio = rollup["spend_split"]["productive_to_abandoned_event_ratio"]
    print(f"\nProductive-to-abandoned event ratio: "
          f"{ratio if ratio is not None else 'n/a (no abandoned spend)'}")
    print()
    print("Cost per released output (proxies)")
    print("| Metric | Value |")
    print("|---|---:|")
    for key, value in rollup["cost_by_released_output"].items():
        print(f"| {key} | {value if value is not None else 'n/a'} |")
    print()
    print(f"Top {limit} tasks by event volume")
    print("| Task | Outcome | Events | Span h | Attempts | Rework |")
    print("|---|---|---:|---:|---:|---:|")
    top = sorted(rollup["tasks"], key=lambda d: d["events_total"], reverse=True)
    for row in top[:limit]:
        print(f"| {row['task_id']} | {row['outcome']} | {row['events_total']} | "
              f"{row['span_hours']} | {row['attempts']} | {row['rework_rounds']} |")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    parser.add_argument("--json", action="store_true", help="Emit rollup as JSON")
    parser.add_argument("--limit", type=int, default=10,
                        help="Detail rows in text output (default 10)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        tasks = load_tasks(args.db)
        events = load_events(args.events)
    except (OSError, sqlite3.Error) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    rollup = build_rollup(tasks, aggregate_events(events))
    if args.json:
        print(json.dumps(rollup, indent=2, sort_keys=True))
    else:
        print_table(rollup, args.limit)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
