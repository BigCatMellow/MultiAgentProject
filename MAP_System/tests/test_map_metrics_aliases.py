#!/usr/bin/env python3
"""Tests for map_metrics event alias normalization."""

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
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES ('codex', 'Codex', 'core', 'available')"
        )
        for event_type in ["APPROVED", "REVIEW_APPROVED", "CHANGES_REQUESTED", "REVIEW_CHANGES_REQUESTED", "task_progress"]:
            conn.execute(
                "INSERT INTO events (event_type, task_id, sender_id, summary) VALUES (?, NULL, 'codex', 'summary')",
                (event_type,),
            )


def test_event_aliases_are_grouped_for_metrics() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        shared = base / "shared"
        shared.mkdir()
        init_db(db)

        result = subprocess.run(
            [sys.executable, str(MAP_METRICS), "--db", str(db), "--shared-dir", str(shared), "--json"],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["event_counts"]["APPROVED"] == 2
        assert payload["event_counts"]["CHANGES_REQUESTED"] == 2
        assert payload["event_counts"]["PROGRESS"] == 1
        assert payload["change_request_rate"] == 0.5


def main() -> int:
    test_event_aliases_are_grouped_for_metrics()
    print("PASS test_event_aliases_are_grouped_for_metrics")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
