#!/usr/bin/env python3
"""Tests for the MAP-only session replay read model."""

from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCRIPT = ROOT / "scripts" / "session_replay.py"
SCHEMA = ROOT / "migration" / "schema.sql"


def init_fixture(base: Path, *, include_bad_event: bool = False, include_missing_ref: bool = False) -> tuple[Path, Path, Path, Path]:
    db_path = base / "map.db"
    task_dir = base / "tasks"
    event_log = base / "events" / "events.jsonl"
    index = base / "runtime" / "session_replay.sqlite"
    task_dir.mkdir(parents=True)
    event_log.parent.mkdir(parents=True)

    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES ('codex-lab-mozu', 'Mozu', 'core', 'available')"
        )
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status, owner, attempt, max_attempts)
            VALUES ('TASK-900', 'TEST', 'Replay task', 'desc', 'implementation', 'engineer', 'APPROVED', 'codex-lab-mozu', 1, 3)
            """
        )

    (task_dir / "TASK-900.json").write_text(
        json.dumps({
            "task_id": "TASK-900",
            "title": "Replay task",
            "status": "APPROVED",
            "owner": "codex-lab-mozu",
            "output_paths": ["out.md"],
            "acceptance_criteria": ["works"],
        }) + "\n",
        encoding="utf-8",
    )

    lines = [
        json.dumps({
            "created_at": "2026-01-01T00:00:00Z",
            "type": "PROGRESS",
            "task_id": "TASK-900",
            "sender": "codex-lab-mozu",
            "summary": "started",
            "artifact_paths": [],
            "trace_id": "task:TASK-900",
            "actor": "codex-lab-mozu",
            "action": "progress",
            "target": "TASK-900",
        }),
        json.dumps({
            "created_at": "2026-01-01T00:01:00Z",
            "type": "SUBMISSION",
            "task_id": "TASK-900",
            "sender": "codex-lab-mozu",
            "summary": "submitted",
            "artifact_paths": ["out.md"],
            "trace_id": "task:TASK-900",
        }),
    ]
    if include_missing_ref:
        lines.append(json.dumps({
            "created_at": "2026-01-01T00:02:00Z",
            "type": "PROGRESS",
            "task_id": "TASK-NOPE",
            "sender": "codex-lab-mozu",
            "summary": "missing task",
            "artifact_paths": [],
        }))
    if include_bad_event:
        lines.append("{bad-json")
    event_log.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return db_path, task_dir, event_log, index


def run_cli(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def load_json(stdout: str) -> dict:
    return json.loads(stdout)


def test_build_creates_disposable_index_and_task_query() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path, task_dir, event_log, index = init_fixture(Path(tmp))
        result = run_cli([
            "--index", str(index),
            "build",
            "--event-log", str(event_log),
            "--task-dir", str(task_dir),
            "--db", str(db_path),
            "--root", str(Path(tmp)),
            "--skip-mirror-validation",
        ])
        assert result.returncode == 0, result.stderr
        payload = load_json(result.stdout)
        assert payload["events_indexed"] == 2
        assert payload["tasks_indexed"] == 1
        assert payload["safe_for_mission_control"] is True
        assert index.exists()

        task = load_json(run_cli(["--index", str(index), "task", "TASK-900"]).stdout)
        assert task["task"]["task_id"] == "TASK-900"
        assert [event["summary"] for event in task["events"]] == ["started", "submitted"]


def test_status_reports_sources_and_drift() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path, task_dir, event_log, index = init_fixture(Path(tmp), include_bad_event=True, include_missing_ref=True)
        build = run_cli([
            "--index", str(index),
            "build",
            "--event-log", str(event_log),
            "--task-dir", str(task_dir),
            "--db", str(db_path),
            "--root", str(Path(tmp)),
            "--skip-mirror-validation",
        ])
        assert build.returncode == 0, build.stderr

        status = load_json(run_cli(["--index", str(index), "status"]).stdout)
        assert status["exists"] is True
        assert status["safe_for_mission_control"] is False
        codes = {finding["code"] for finding in status["drift_findings"]}
        assert "malformed_event" in codes
        assert "missing_task_ref" in codes
        sources = {snapshot["source"] for snapshot in status["source_snapshots"]}
        assert {"map_events_jsonl", "map_db", "task_json"} <= sources


def test_build_records_mirror_validation_failure_when_enabled() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path, task_dir, event_log, index = init_fixture(Path(tmp))
        result = run_cli([
            "--index", str(index),
            "build",
            "--event-log", str(event_log),
            "--task-dir", str(task_dir),
            "--db", str(db_path),
            "--root", str(Path(tmp)),
        ])
        assert result.returncode == 0, result.stderr

        status = load_json(run_cli(["--index", str(index), "status"]).stdout)
        codes = {finding["code"] for finding in status["drift_findings"]}
        assert "mirror_validation_failed" in codes
        assert status["safe_for_mission_control"] is False


def test_agent_and_trace_queries_are_deterministic_json() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path, task_dir, event_log, index = init_fixture(Path(tmp))
        run_cli([
            "--index", str(index),
            "build",
            "--event-log", str(event_log),
            "--task-dir", str(task_dir),
            "--db", str(db_path),
            "--root", str(Path(tmp)),
            "--skip-mirror-validation",
        ])

        agent = load_json(run_cli(["--index", str(index), "agent", "codex-lab-mozu"]).stdout)
        trace = load_json(run_cli(["--index", str(index), "trace", "task:TASK-900"]).stdout)

        assert agent["agent"]["agent_id"] == "codex-lab-mozu"
        assert len(agent["events"]) == 2
        assert [event["replay_id"] for event in trace["events"]] == ["map-events:1", "map-events:2"]


def main() -> int:
    for test in [
        test_build_creates_disposable_index_and_task_query,
        test_status_reports_sources_and_drift,
        test_build_records_mirror_validation_failure_when_enabled,
        test_agent_and_trace_queries_are_deterministic_json,
    ]:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
