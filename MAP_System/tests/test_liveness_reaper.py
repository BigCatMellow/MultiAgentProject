#!/usr/bin/env python3
"""Tests for the liveness reaper (TASK-158, from TASK-150's spec)."""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.liveness_reaper import (  # noqa: E402
    classify_state,
    build_snapshot,
    render_snapshot_markdown,
    reclaim_stale_claims,
    dead_letter_task,
    replay_dead_letter,
    normalize_hcom_status,
    DeadLetterReplayError,
    STATES,
)

import shutil

NOW = datetime(2026, 7, 13, 12, 0, 0, tzinfo=timezone.utc)


def test_declared_standby_wins_over_hcom() -> None:
    record = classify_state(
        "codex-lab-limo",
        {"status": "standby", "reason": "awaiting_work"},
        {"status": "listening", "status_age_seconds": 5},
        None,
        NOW,
    )
    assert record.state == "standby"


def test_working_when_claimed_task_and_live_hcom() -> None:
    record = classify_state(
        "codex-lab-mozu",
        {"status": "available"},
        {"status": "active", "status_age_seconds": 10},
        ("TASK-152", "IN_PROGRESS"),
        NOW,
    )
    assert record.state == "working"
    assert record.active_task == "TASK-152"


def test_suspect_when_hcom_stale() -> None:
    record = classify_state(
        "claude-lab-vino",
        {"status": "available"},
        {"status": "listening", "status_age_seconds": 5000},
        None,
        NOW,
    )
    assert record.state == "suspect"


def test_idle_when_live_but_no_claim_beyond_checkin_threshold() -> None:
    record = classify_state(
        "claude-lab-magi",
        {"status": "available"},
        {"status": "listening", "status_age_seconds": 5, "idle_seconds": 8000},
        None,
        NOW,
    )
    assert record.state == "idle"


def test_broken_when_no_hcom_data_and_active_task() -> None:
    record = classify_state(
        "claude-lab-ghost",
        {"status": "available"},
        None,
        ("TASK-999", "IN_PROGRESS"),
        NOW,
    )
    assert record.state == "broken"


def test_all_states_in_vocabulary() -> None:
    cases = [
        classify_state("a", {"status": "standby"}, None, None, NOW),
        classify_state("b", {"status": "available"}, {"status": "active", "status_age_seconds": 1}, ("T", "IN_PROGRESS"), NOW),
        classify_state("c", {"status": "available"}, {"status": "blocked", "status_age_seconds": 1}, None, NOW),
        classify_state("d", {"status": "available"}, {"status": "listening", "status_age_seconds": 5, "idle_seconds": 8000}, None, NOW),
        classify_state("e", {"status": "available"}, {"status": "listening", "status_age_seconds": 5000}, None, NOW),
        classify_state("f", {"status": "available"}, None, ("T", "IN_PROGRESS"), NOW),
        classify_state("g", {"status": "available"}, {"status": "listening", "status_age_seconds": 1}, None, NOW),
    ]
    for c in cases:
        assert c.state in STATES, f"{c.agent_id}: unexpected state {c.state}"


def test_build_snapshot_and_render_markdown() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        status_path = Path(tmp) / "status.json"
        status_path.write_text(json.dumps({
            "agents": {
                "test-agent-a": {"status": "available", "reason": None},
                "test-agent-b": {"status": "standby", "reason": "awaiting_work"},
            }
        }), encoding="utf-8")

        db_path = Path(tmp) / "map.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE tasks (task_id TEXT, status TEXT, claimed_by TEXT, lease_expires_at TEXT)"
        )
        conn.execute(
            "INSERT INTO tasks VALUES ('TASK-X', 'IN_PROGRESS', 'test-agent-a', NULL)"
        )
        conn.commit()
        conn.close()

        hcom_status = {"test-agent-a": {"status": "active", "status_age_seconds": 5}}
        records = build_snapshot(status_path, hcom_status, db_path, now=NOW)
        assert len(records) == 2
        by_id = {r.agent_id: r for r in records}
        assert by_id["test-agent-a"].state == "working"
        assert by_id["test-agent-a"].active_task == "TASK-X"
        assert by_id["test-agent-b"].state == "standby"

        markdown = render_snapshot_markdown(records, now=NOW)
        assert "test-agent-a" in markdown
        assert "working" in markdown
        assert "hpom: file: shared/liveness-state.md" in markdown


def test_reclaim_stale_claims_dry_run_does_not_mutate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "map.db"
        conn = sqlite3.connect(db_path)
        conn.execute(
            "CREATE TABLE tasks (task_id TEXT, status TEXT, claimed_by TEXT, lease_expires_at TEXT)"
        )
        conn.execute(
            "INSERT INTO tasks VALUES ('TASK-STALE', 'IN_PROGRESS', 'ghost-agent', '2020-01-01T00:00:00')"
        )
        conn.commit()
        conn.close()

        candidates = reclaim_stale_claims(db_path, dry_run=True)
        assert candidates == ["TASK-STALE"]

        conn = sqlite3.connect(db_path)
        status = conn.execute("SELECT status FROM tasks WHERE task_id = 'TASK-STALE'").fetchone()[0]
        conn.close()
        assert status == "IN_PROGRESS", "dry-run must not mutate task status"


def test_dead_letter_task_appends_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dl_log = Path(tmp) / "dead_letters.jsonl"
        event_log = Path(tmp) / "events.jsonl"
        dl_id = dead_letter_task(
            "TASK-BROKEN", "ghost-agent", "stale heartbeat, no resume response",
            dead_letter_log=dl_log, event_log=event_log,
        )

        assert dl_log.exists()
        record = json.loads(dl_log.read_text(encoding="utf-8").splitlines()[0])
        assert record["task_id"] == "TASK-BROKEN"
        assert record["dead_letter_id"] == dl_id
        assert record["replay_status"] == "pending"
        assert dl_id in record["replay_command"]

        assert event_log.exists()
        event = json.loads(event_log.read_text(encoding="utf-8").splitlines()[0])
        assert event["task_id"] == "TASK-158"
        assert event["action"] == "dead_letter"


def _make_fixture_db(tmp: Path) -> tuple[Path, Path]:
    """Isolated copy of the real map.db + a fresh output dir for mirrors,
    so reclaim/replay tests never touch canonical MAP_System state.
    """
    fixture_db = Path(tmp) / "fixture-map.db"
    shutil.copy(REPO / "MAP_System" / "map.db", fixture_db)
    mirror_root = Path(tmp) / "mirror-out"
    mirror_root.mkdir()
    return fixture_db, mirror_root


def _insert_fixture_task(db_path: Path, task_id: str, status: str, claimed_by: str, lease_expires_at: str | None) -> None:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute(
        "INSERT INTO agents (agent_id, label, status) VALUES (?, ?, 'available') ON CONFLICT(agent_id) DO NOTHING",
        (claimed_by, claimed_by),
    )
    conn.execute(
        """
        INSERT INTO tasks (task_id, project_id, title, task_type, role, status, owner, claimed_by, lease_expires_at, attempt, max_attempts)
        VALUES (?, 'MAP-BOOTSTRAP-20260617', ?, 'implementation', 'implementer', ?, 'command-center', ?, ?, 1, 3)
        """,
        (task_id, f"Fixture task {task_id}", status, claimed_by, lease_expires_at),
    )
    conn.commit()
    conn.close()


def test_reclaim_with_act_exports_and_validates_mirrors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fixture_db, mirror_root = _make_fixture_db(Path(tmp))
        fixture_event_log = Path(tmp) / "events.jsonl"
        task_id = "TASK-FIXTURE-RECLAIM-1"
        _insert_fixture_task(fixture_db, task_id, "IN_PROGRESS", "ghost-agent", "2020-01-01T00:00:00")

        reclaimed = reclaim_stale_claims(
            fixture_db, dry_run=False, repo_root=REPO, mirror_root=mirror_root,
            event_log=fixture_event_log,
        )
        assert task_id in reclaimed

        exported_task_path = mirror_root / "tasks" / f"{task_id}.json"
        assert exported_task_path.exists(), "reclaim must export file mirrors, not just mutate SQLite"
        exported = json.loads(exported_task_path.read_text(encoding="utf-8"))
        assert exported["status"] == "READY"

        conn = sqlite3.connect(fixture_db)
        status = conn.execute("SELECT status, claimed_by FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        conn.close()
        assert status == ("READY", None)

        assert fixture_event_log.exists()
        events = [
            json.loads(line)
            for line in fixture_event_log.read_text(encoding="utf-8").splitlines()
        ]
        event = next(event for event in events if event.get("target") == task_id)
        assert task_id in event["summary"]


def test_replay_dead_letter_requeues_and_exports_mirrors() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        fixture_db, mirror_root = _make_fixture_db(Path(tmp))
        dl_log = Path(tmp) / "dead_letters.jsonl"
        event_log = Path(tmp) / "events.jsonl"
        task_id = "TASK-FIXTURE-RECLAIM-2"
        # Not lease-expired -- simulates a task the reaper decided to
        # dead-letter for a reason other than plain lease expiry (context
        # would be lost by a bare reclaim).
        _insert_fixture_task(fixture_db, task_id, "IN_PROGRESS", "broken-agent", None)

        dl_id = dead_letter_task(task_id, "broken-agent", "agent went broken mid-task", dl_log, event_log)

        result = replay_dead_letter(
            dl_id, dead_letter_log=dl_log, db_path=fixture_db, event_log=event_log,
            repo_root=REPO, mirror_root=mirror_root,
        )
        assert result["replay_status"] == "replayed"

        exported_task_path = mirror_root / "tasks" / f"{task_id}.json"
        assert exported_task_path.exists()
        assert json.loads(exported_task_path.read_text(encoding="utf-8"))["status"] == "READY"

        conn = sqlite3.connect(fixture_db)
        status = conn.execute("SELECT status, claimed_by FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        conn.close()
        assert status == ("READY", None)

        # Replaying the same dead_letter_id twice must not silently re-apply.
        try:
            replay_dead_letter(dl_id, dead_letter_log=dl_log, db_path=fixture_db, event_log=event_log, repo_root=REPO, mirror_root=mirror_root)
            raise AssertionError("expected DeadLetterReplayError on double-replay")
        except DeadLetterReplayError:
            pass


def test_replay_dead_letter_refuses_unknown_id() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        dl_log = Path(tmp) / "dead_letters.jsonl"
        dl_log.write_text("", encoding="utf-8")
        try:
            replay_dead_letter("DL-nonexistent", dead_letter_log=dl_log)
            raise AssertionError("expected DeadLetterReplayError")
        except DeadLetterReplayError:
            pass


def test_normalize_hcom_status_passes_through_agent_keyed_dict() -> None:
    raw = {"agent-a": {"status": "active", "status_age_seconds": 5}}
    assert normalize_hcom_status(raw) == raw


def test_normalize_hcom_status_converts_raw_hcom_list_shape() -> None:
    """TASK-175's runtime-exercise audit found `hcom list --json`'s real
    output shape (a list of session records keyed by 'name') crashes
    build_snapshot() with AttributeError -- reproduced independently
    during TASK-175's review before this fix.
    """
    raw = [
        {"name": "codex-lab-mozu", "status": "active", "status_age_seconds": 0, "status_detail": "tool:Bash"},
        {"name": "claude-lab-zera", "status": "listening", "status_age_seconds": 12, "description": "idle"},
    ]
    normalized = normalize_hcom_status(raw)
    assert normalized["codex-lab-mozu"]["status"] == "active"
    assert normalized["codex-lab-mozu"]["last_seen"] == "tool:Bash"
    assert normalized["claude-lab-zera"]["status"] == "listening"
    assert normalized["claude-lab-zera"]["last_seen"] == "idle"


def test_normalize_hcom_status_skips_records_without_a_name() -> None:
    raw = [{"status": "active"}, {"name": "real-agent", "status": "active"}]
    normalized = normalize_hcom_status(raw)
    assert list(normalized.keys()) == ["real-agent"]


def test_normalize_hcom_status_rejects_unknown_shape() -> None:
    try:
        normalize_hcom_status("not a dict or list")  # type: ignore[arg-type]
        raise AssertionError("expected TypeError")
    except TypeError:
        pass


def test_build_snapshot_works_with_raw_hcom_list_via_normalize() -> None:
    """End-to-end regression: build_snapshot() must not crash when fed the
    real hcom list --json shape through normalize_hcom_status() first --
    this is the actual fix path main() now uses.
    """
    with tempfile.TemporaryDirectory() as tmp:
        status_path = Path(tmp) / "status.json"
        status_path.write_text(json.dumps({
            "agents": {"codex-lab-mozu": {"status": "available", "reason": None}}
        }), encoding="utf-8")
        db_path = Path(tmp) / "map.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE tasks (task_id TEXT, status TEXT, claimed_by TEXT, lease_expires_at TEXT)")
        conn.commit()
        conn.close()

        raw_hcom_list = [{"name": "codex-lab-mozu", "status": "active", "status_age_seconds": 0}]
        normalized = normalize_hcom_status(raw_hcom_list)
        records = build_snapshot(status_path, normalized, db_path, now=NOW)
        by_id = {r.agent_id: r for r in records}
        assert by_id["codex-lab-mozu"].state == "alive"


def main() -> int:
    tests = [
        test_declared_standby_wins_over_hcom,
        test_working_when_claimed_task_and_live_hcom,
        test_suspect_when_hcom_stale,
        test_idle_when_live_but_no_claim_beyond_checkin_threshold,
        test_broken_when_no_hcom_data_and_active_task,
        test_all_states_in_vocabulary,
        test_build_snapshot_and_render_markdown,
        test_reclaim_stale_claims_dry_run_does_not_mutate,
        test_dead_letter_task_appends_record,
        test_reclaim_with_act_exports_and_validates_mirrors,
        test_replay_dead_letter_requeues_and_exports_mirrors,
        test_replay_dead_letter_refuses_unknown_id,
        test_normalize_hcom_status_passes_through_agent_keyed_dict,
        test_normalize_hcom_status_converts_raw_hcom_list_shape,
        test_normalize_hcom_status_skips_records_without_a_name,
        test_normalize_hcom_status_rejects_unknown_shape,
        test_build_snapshot_works_with_raw_hcom_list_via_normalize,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
