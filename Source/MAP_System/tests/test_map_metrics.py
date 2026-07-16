#!/usr/bin/env python3
"""Tests for MAP health metrics reporting."""

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
MAP_METRICS = ROOT / "scripts" / "map_metrics.py"


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES "
            "('codex-live', 'Codex Live', 'core', 'available')"
        )
        statuses = ["READY", "SUBMITTED", "SUBMITTED", "CONFLICT", "APPROVED"]
        for index, status in enumerate(statuses, start=1):
            conn.execute(
                """
                INSERT INTO tasks
                  (task_id, project_id, title, description, task_type, role,
                   status, owner, attempt, max_attempts)
                VALUES (?, 'TEST', ?, 'desc', 'implementation', 'implementer',
                        ?, 'codex-live', 0, 3)
                """,
                (f"TASK-M{index}", f"Task {index}", status),
            )
        conn.execute(
            "INSERT INTO events (event_type, task_id, sender_id, summary) VALUES "
            "('APPROVED', 'TASK-M5', 'codex-live', 'approved')"
        )
        conn.execute(
            "INSERT INTO events (event_type, task_id, sender_id, summary) VALUES "
            "('CHANGES_REQUESTED', 'TASK-M2', 'codex-live', 'changes')"
        )


def init_shared(path: Path) -> None:
    path.mkdir(parents=True)
    (path / "state.md").write_text(
        "\n".join(
            [
                "<!-- hpom: file: shared/state.md -->",
                "<!-- hpom: project: MAP -->",
                "<!-- hpom: state_owner: command-center -->",
                "<!-- hpom: status: NEEDS_REVIEW -->",
                "<!-- hpom: last_verified: 2026-06-29 -->",
                "<!-- hpom: verified_against: test -->",
                "<!-- hpom: confidence: LOW -->",
                "<!-- hpom: supersedes: NONE -->",
                "<!-- hpom: superseded_by: NONE -->",
                "",
                "# State",
            ]
        ),
        encoding="utf-8",
    )


def run_metrics(db: Path, shared: Path, *, as_json: bool) -> subprocess.CompletedProcess:
    cmd = [sys.executable, str(MAP_METRICS), "--db", str(db), "--shared-dir", str(shared)]
    if as_json:
        cmd.append("--json")
    return subprocess.run(cmd, cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def test_json_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        shared = base / "shared"
        init_db(db)
        init_shared(shared)

        result = run_metrics(db, shared, as_json=True)

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["task_counts"]["SUBMITTED"] == 2
        assert payload["review_queue_size"] == 2
        assert payload["conflict_count"] == 1
        assert payload["stale_shared_file_count"] == 1
        assert payload["change_request_rate"] == 0.5


def test_text_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        shared = base / "shared"
        init_db(db)
        init_shared(shared)

        result = run_metrics(db, shared, as_json=False)

        assert result.returncode == 0, result.stderr
        assert "Task counts by status" in result.stdout
        assert "| SUBMITTED | 2 |" in result.stdout
        assert "| Conflict count | 1 |" in result.stdout


def main() -> int:
    for test in [test_json_metrics, test_text_metrics]:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
