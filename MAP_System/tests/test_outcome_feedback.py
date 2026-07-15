#!/usr/bin/env python3
"""Outcome feedback event validation and blind-spot metrics (TASK-189)."""

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
VALIDATE_EVENTS = ROOT / "scripts" / "validate_events.py"
MAP_METRICS = ROOT / "scripts" / "map_metrics.py"


def outcome_payload(
    outcome_id: str,
    *,
    status: str,
    validation_status: str = "passed",
    review_status: str = "approved",
    follow_up: str = "none",
    failure_class: str | None = None,
) -> dict:
    payload = {
        "outcome_id": outcome_id,
        "observed_at": "2026-07-14T22:00:00Z",
        "observed_by": "codex-lab-test",
        "outcome_status": status,
        "validation_status_at_ship": validation_status,
        "review_status_at_ship": review_status,
        "follow_up": follow_up,
        "use_context": "focused test",
        "evidence_paths": ["MAP_System/tests/test_outcome_feedback.py"],
    }
    if failure_class:
        payload["failure_class"] = failure_class
        payload["severity"] = "BLOCKING"
    return payload


def validate_event_log(lines: list[dict]) -> subprocess.CompletedProcess:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "events.jsonl"
        baseline = Path(tmp) / "warning_baseline.json"
        log.write_text(
            "".join(json.dumps(line, separators=(",", ":")) + "\n" for line in lines),
            encoding="utf-8",
        )
        baseline.write_text('{"baseline_line_count":0}\n', encoding="utf-8")
        return subprocess.run(
            [
                sys.executable,
                str(VALIDATE_EVENTS),
                "--event-log",
                str(log),
                "--warning-baseline",
                str(baseline),
                "--fail-on-new",
            ],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )


def test_outcome_events_validate_with_top_level_or_summary_payload() -> None:
    top_level = {
        "created_at": "2026-07-14T22:01:00Z",
        "type": "outcome_pass",
        "task_id": "TASK-1",
        "sender": "codex-lab-test",
        "summary": "later use passed",
        "artifact_paths": [],
        **outcome_payload("OUT-1", status="pass"),
    }
    summary_payload = {
        "created_at": "2026-07-14T22:02:00Z",
        "type": "outcome_fail",
        "task_id": "TASK-2",
        "sender": "codex-lab-test",
        "summary": json.dumps(
            outcome_payload(
                "OUT-2",
                status="fail",
                follow_up="validator_improvement",
                failure_class="validator_blind_spot",
            ),
            separators=(",", ":"),
        ),
        "artifact_paths": ["MAP_System/repairs/REPAIR-TEST.md"],
    }

    result = validate_event_log([top_level, summary_payload])

    assert result.returncode == 0, result.stdout + result.stderr
    assert "new_warnings=0" in result.stdout


def test_outcome_event_validation_rejects_bad_shape() -> None:
    bad = {
        "created_at": "2026-07-14T22:03:00Z",
        "type": "outcome_fail",
        "task_id": "TASK-3",
        "sender": "codex-lab-test",
        "summary": json.dumps(
            {
                "outcome_id": "OUT-3",
                "outcome_status": "broken",
                "validation_status_at_ship": "passed",
                "review_status_at_ship": "approved",
                "follow_up": "validator_improvement",
            }
        ),
        "artifact_paths": [],
    }

    result = validate_event_log([bad])

    assert result.returncode == 1
    assert "outcome event missing field(s): observed_at, observed_by" in result.stdout
    assert "outcome field outcome_status has invalid value" in result.stdout


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES "
            "('codex-lab-test', 'Codex Lab Test', 'core', 'available')"
        )
        for task_id in ("TASK-1", "TASK-2", "TASK-3", "TASK-4"):
            conn.execute(
                """
                INSERT INTO tasks
                  (task_id, project_id, title, description, task_type, role,
                   status, owner, attempt, max_attempts)
                VALUES (?, 'TEST', ?, 'desc', 'implementation', 'implementer',
                        'RELEASED', 'codex-lab-test', 0, 3)
                """,
                (task_id, task_id),
            )


def insert_outcome(conn: sqlite3.Connection, event_type: str, task_id: str, payload: dict) -> None:
    conn.execute(
        """
        INSERT INTO events (event_type, task_id, sender_id, summary, artifact_paths)
        VALUES (?, ?, 'codex-lab-test', ?, '[]')
        """,
        (event_type, task_id, json.dumps(payload, separators=(",", ":"))),
    )


def test_map_metrics_reports_validator_blind_spot_rate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        shared = base / "shared"
        shared.mkdir()
        init_db(db)
        with sqlite3.connect(db) as conn:
            insert_outcome(conn, "outcome_pass", "TASK-1", outcome_payload("OUT-1", status="pass"))
            insert_outcome(
                conn,
                "outcome_fail",
                "TASK-2",
                outcome_payload(
                    "OUT-2",
                    status="fail",
                    follow_up="validator_improvement",
                    failure_class="validator_blind_spot",
                ),
            )
            insert_outcome(
                conn,
                "outcome_fail",
                "TASK-3",
                outcome_payload("OUT-3", status="fail", validation_status="failed"),
            )
            insert_outcome(
                conn,
                "outcome_pass",
                "TASK-4",
                outcome_payload("OUT-4", status="not_exercised"),
            )

        result = subprocess.run(
            [sys.executable, str(MAP_METRICS), "--db", str(db), "--shared-dir", str(shared), "--json"],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        feedback = payload["outcome_feedback"]
        assert feedback["outcome_event_count"] == 4
        assert feedback["validator_blind_spot_count"] == 1
        assert feedback["validator_blind_spot_denominator"] == 2
        assert feedback["validator_blind_spot_rate"] == 0.5
        assert payload["event_counts"]["outcome_fail"] == 2
        assert payload["event_counts"]["outcome_pass"] == 2


def test_map_metrics_text_includes_validator_blind_spot_rate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        shared = base / "shared"
        shared.mkdir()
        init_db(db)
        with sqlite3.connect(db) as conn:
            insert_outcome(conn, "outcome_fail", "TASK-1", outcome_payload("OUT-1", status="fail"))

        result = subprocess.run(
            [sys.executable, str(MAP_METRICS), "--db", str(db), "--shared-dir", str(shared)],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        assert result.returncode == 0, result.stderr
        assert "| Validator blind-spot rate | 100.00% |" in result.stdout
        assert "| Validator blind-spot count | 1 / 1 |" in result.stdout


def main() -> int:
    tests = [
        test_outcome_events_validate_with_top_level_or_summary_payload,
        test_outcome_event_validation_rejects_bad_shape,
        test_map_metrics_reports_validator_blind_spot_rate,
        test_map_metrics_text_includes_validator_blind_spot_rate,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} outcome feedback tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
