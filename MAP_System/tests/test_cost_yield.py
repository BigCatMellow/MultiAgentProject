#!/usr/bin/env python3
"""Tests for the cost/yield rollup (TASK-190). Fixture db + events.jsonl."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCHEMA = ROOT / "migration" / "schema.sql"
COST_YIELD = ROOT / "scripts" / "cost_yield.py"

sys.path.insert(0, str(ROOT / "scripts"))

from cost_yield import aggregate_events, build_rollup, classify_outcome, parse_ts


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES "
            "('codex-live', 'Codex Live', 'core', 'available')"
        )
        rows = [
            ("TASK-Y1", "Released work", "RELEASED", 1),
            ("TASK-Y2", "Approved awaiting release", "APPROVED", 1),
            ("TASK-Y3", "Retired duplicate", "RETIRED", 1),
            ("TASK-Y4", "Legacy bootstrap", "DONE", 1),
            ("TASK-Y5", "Still open", "IN_PROGRESS", 2),
            ("TASK-Y6", "Second release", "RELEASED", 3),
        ]
        for task_id, title, status, attempt in rows:
            conn.execute(
                """
                INSERT INTO tasks
                  (task_id, project_id, title, description, task_type, role,
                   status, owner, attempt, max_attempts)
                VALUES (?, 'TEST', ?, 'desc', 'implementation', 'implementer',
                        ?, 'codex-live', ?, 3)
                """,
                (task_id, title, status, attempt),
            )


def fixture_events() -> list[dict]:
    ev = lambda ts, etype, tid: {
        "created_at": ts, "type": etype, "task_id": tid,
        "sender": "codex-live", "summary": "s", "artifact_paths": [],
    }
    return [
        # TASK-Y1: full lifecycle over 4h, one rework round (alias form)
        ev("2026-07-10T10:00:00Z", "PROGRESS", "TASK-Y1"),
        ev("2026-07-10T11:00:00Z", "SUBMISSION", "TASK-Y1"),
        ev("2026-07-10T12:00:00Z", "REVIEW_CHANGES_REQUESTED", "TASK-Y1"),
        ev("2026-07-10T13:00:00Z", "REVIEW_APPROVED", "TASK-Y1"),
        ev("2026-07-10T14:00:00Z", "RELEASED", "TASK-Y1"),
        # TASK-Y3 (retired): 2 events across 1h, mixed offset formats
        ev("2026-07-10T06:00:00-04:00", "PROGRESS", "TASK-Y3"),
        ev("2026-07-10T11:00:00Z", "PROGRESS", "TASK-Y3"),
        # TASK-Y5 (in flight): 1 event
        ev("2026-07-11T10:00:00Z", "PROGRESS", "TASK-Y5"),
        # TASK-Y6 (released): 2 events
        ev("2026-07-12T10:00:00Z", "PROGRESS", "TASK-Y6"),
        ev("2026-07-12T10:30:00Z", "RELEASED", "TASK-Y6"),
        # unattributed + unknown task id
        ev("2026-07-10T09:00:00Z", "DECISION_RECORDED", None),
        ev("2026-07-10T09:30:00Z", "PROGRESS", "TASK-GHOST"),
    ]


def write_events(path: Path) -> None:
    path.write_text("\n".join(json.dumps(e) for e in fixture_events()) + "\n",
                    encoding="utf-8")


def run_rollup(db: Path, events: Path, *extra: str) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(COST_YIELD), "--db", str(db), "--events", str(events),
           *extra]
    return subprocess.run(cmd, cwd=REPO, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_outcome_classification() -> None:
    assert classify_outcome("RELEASED") == "released"
    assert classify_outcome("APPROVED") == "approved_not_released"
    assert classify_outcome("RETIRED") == "retired"
    # DONE is legacy pre-release-gate history, NOT abandoned spend
    assert classify_outcome("DONE") == "legacy_done"
    # unknown terminal statuses are abandoned (terminal-but-unreleased)
    assert classify_outcome("FAILED") == "abandoned"
    assert classify_outcome("CANCELLED") == "abandoned"
    # anything non-terminal is in flight
    for status in ("BACKLOG", "READY", "IN_PROGRESS", "SUBMITTED",
                   "CHANGES_REQUESTED", "CONFLICT", None):
        assert classify_outcome(status) == "in_flight"


def test_aggregate_events_aliases_and_lifecycle() -> None:
    per_task = aggregate_events(fixture_events())

    y1 = per_task["TASK-Y1"]
    assert y1["events_total"] == 5
    # alias normalization folds REVIEW_* into the canonical types
    assert y1["event_counts"]["CHANGES_REQUESTED"] == 1
    assert y1["event_counts"]["APPROVED"] == 1
    assert y1["submitted_at"] < y1["approved_at"] < y1["released_at"]
    assert y1["first_event_at"] == parse_ts("2026-07-10T10:00:00Z")
    assert y1["last_event_at"] == parse_ts("2026-07-10T14:00:00Z")

    # mixed offset formats compare correctly: 06:00-04:00 == 10:00Z < 11:00Z
    y3 = per_task["TASK-Y3"]
    assert y3["first_event_at"] == parse_ts("2026-07-10T10:00:00Z")
    assert y3["last_event_at"] == parse_ts("2026-07-10T11:00:00Z")

    assert per_task[None]["events_total"] == 1
    assert per_task["TASK-GHOST"]["events_total"] == 1


def test_rollup_split_and_released_cost() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db)
        from cost_yield import load_tasks
        rollup = build_rollup(load_tasks(db), aggregate_events(fixture_events()))

    classes = rollup["outcome_classes"]
    assert classes["released"]["tasks"] == 2
    assert classes["released"]["events"] == 7
    assert classes["released"]["rework_rounds"] == 1
    assert classes["approved_not_released"]["tasks"] == 1
    assert classes["retired"]["tasks"] == 1
    assert classes["legacy_done"]["tasks"] == 1
    assert classes["in_flight"]["tasks"] == 1
    assert classes["abandoned"]["tasks"] == 0
    assert classes["released"]["statuses"] == {"RELEASED": 2}

    # attributed = 7 released + 2 retired + 1 in-flight; ghost/None excluded
    assert rollup["totals"]["events_attributed"] == 10
    assert rollup["totals"]["events_unattributed"] == 1
    assert rollup["totals"]["events_unknown_task"] == 1
    assert rollup["unknown_task_ids"] == ["TASK-GHOST"]

    split = rollup["spend_split"]
    assert split["productive"]["events"] == 7
    assert split["productive"]["event_percent"] == 70.0
    assert split["abandoned"]["events"] == 2
    assert split["pending"]["tasks"] == 2
    assert split["legacy"]["tasks"] == 1
    assert split["productive_to_abandoned_event_ratio"] == 3.5

    cost = rollup["cost_by_released_output"]
    assert cost["released_tasks"] == 2
    assert cost["events_per_released_task_avg"] == 3.5   # (5+2)/2
    assert cost["span_hours_per_released_task_avg"] == 2.25  # (4.0+0.5)/2
    assert cost["attempts_per_released_task_avg"] == 2.0  # (1+3)/2
    assert cost["all_in_events_per_release"] == 5.0       # 10 attributed / 2

    y1 = next(d for d in rollup["tasks"] if d["task_id"] == "TASK-Y1")
    assert y1["span_hours"] == 4.0
    assert y1["rework_rounds"] == 1
    assert y1["lifecycle"]["released_at"] is not None


def test_zero_released_yields_no_division() -> None:
    """No released tasks (or no abandoned spend) must not crash the ratios."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        with sqlite3.connect(db) as conn:
            conn.executescript(SCHEMA.read_text(encoding="utf-8"))
            conn.execute(
                "INSERT INTO tasks (task_id, project_id, title, description, "
                "task_type, role, status, attempt, max_attempts) VALUES "
                "('TASK-Z1', 'TEST', 't', 'd', 'implementation', 'implementer', "
                "'READY', 1, 3)")
        from cost_yield import load_tasks
        rollup = build_rollup(load_tasks(db), aggregate_events([]))

    assert rollup["cost_by_released_output"]["released_tasks"] == 0
    assert rollup["cost_by_released_output"]["all_in_events_per_release"] is None
    assert rollup["spend_split"]["productive_to_abandoned_event_ratio"] is None
    assert rollup["outcome_classes"]["released"]["event_percent"] == 0.0


def test_cli_json_and_text() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        events = base / "events.jsonl"
        init_db(db)
        write_events(events)

        result = run_rollup(db, events, "--json")
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["outcome_classes"]["released"]["tasks"] == 2
        assert payload["spend_split"]["productive"]["event_percent"] == 70.0
        assert "PROXIES" in payload["proxy_note"]

        result = run_rollup(db, events)
        assert result.returncode == 0, result.stderr
        assert "MAP Cost/Yield Rollup" in result.stdout
        assert "PROXIES" in result.stdout          # proxies labeled, no dollars
        assert "$" not in result.stdout            # no fabricated currency
        assert "| released | 2 | 7 |" in result.stdout
        assert "Productive vs abandoned split" in result.stdout
        assert "| TASK-Y1 | released | 5 |" in result.stdout

        result = run_rollup(base / "missing.db", events, "--json")
        assert result.returncode == 1
        assert "error:" in result.stderr


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} cost_yield tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
