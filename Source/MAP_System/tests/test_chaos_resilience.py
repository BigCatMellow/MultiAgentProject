#!/usr/bin/env python3
"""Executable chaos probes for TASK-161's 6 named scenarios (from
map-613-master-implementation-plan.md Wave 7 item 4 and
map-resilience-controls-spec.md).

Every probe here runs against an isolated fixture copy of map.db or a
disposable temp log -- never canonical MAP_System state, per the migration
plan's explicit chaos-testing safety rule (map-runtime-migration-plan.md
Step 7).
"""

from __future__ import annotations

import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.durable_execution import (  # noqa: E402
    record_checkpoint,
    resume_step,
)
from MAP_System.scripts.validate_protocol import evaluate_protocol  # noqa: E402
from MAP_System.scripts.liveness_reaper import reclaim_stale_claims  # noqa: E402
from MAP_System.scripts.dead_letter_queue import enqueue, replay, DeadLetterError  # noqa: E402


def _make_fixture_db(tmp: Path) -> tuple[Path, Path]:
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
        (task_id, f"Chaos fixture {task_id}", status, claimed_by, lease_expires_at),
    )
    conn.commit()
    conn.close()


def test_chaos_1_killed_handler_mid_task() -> None:
    """A handler crashes right after the 'claim' step, before 'handler'
    completes. A resumed process must pick up at 'handler', not restart
    at 'claim' or silently skip ahead.
    """
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "checkpoints.jsonl"
        record_checkpoint("TASK-CHAOS-1", "claim", log=log)
        assert resume_step("TASK-CHAOS-1", log) == "handler"


def test_chaos_2_stale_mirror_detected() -> None:
    """A task_graph.json mirror drifts from SQLite (simulating a crash
    between a DB write and its mirror export). validate_task_mirrors.py
    must detect this as a real failure, not pass silently.
    """
    with tempfile.TemporaryDirectory() as tmp:
        fixture_db, mirror_root = _make_fixture_db(Path(tmp))
        task_id = "TASK-CHAOS-2"
        _insert_fixture_task(fixture_db, task_id, "READY", "nobody", None)

        # Deliberately do NOT export mirrors after the DB insert -- this
        # is the stale-mirror condition: task_graph.json under mirror_root
        # was never created, so it disagrees with the DB's task list.
        import subprocess
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_task_mirrors.py"), "--db", str(fixture_db), "--root", str(mirror_root)],
            cwd=REPO, text=True, capture_output=True, check=False,
        )
        assert result.returncode != 0, "validate_task_mirrors.py must fail on a genuinely stale/missing mirror"


def test_chaos_3_malformed_protocol_output_detected() -> None:
    """A message uses an unrecognized MATOCP token -- the protocol
    validator must flag it, not silently accept malformed shorthand.
    """
    finding = evaluate_protocol("!UNKNOWN_TOKEN something bad")
    assert finding["passed"] is False
    assert finding["adjudication"] == "pending"


def test_chaos_4_hung_agent_reaper_path() -> None:
    """A hung agent's lease expires. The liveness reaper must reclaim the
    task back to READY and leave mirrors consistent -- the direct
    end-to-end test of the reaper's real (not dry-run) action path.
    """
    with tempfile.TemporaryDirectory() as tmp:
        fixture_db, mirror_root = _make_fixture_db(Path(tmp))
        event_log = Path(tmp) / "events.jsonl"
        task_id = "TASK-CHAOS-4"
        _insert_fixture_task(fixture_db, task_id, "IN_PROGRESS", "hung-agent", "2020-01-01T00:00:00")

        reclaimed = reclaim_stale_claims(
            fixture_db, dry_run=False, repo_root=REPO, mirror_root=mirror_root, event_log=event_log,
        )
        assert task_id in reclaimed

        conn = sqlite3.connect(fixture_db)
        status = conn.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,)).fetchone()[0]
        conn.close()
        assert status == "READY"


def test_chaos_5_mid_task_resume_after_multiple_completed_steps() -> None:
    """Distinct from chaos-1: here several steps completed before the
    crash, so resume must continue from the LATEST checkpoint, not the
    first one.
    """
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "checkpoints.jsonl"
        record_checkpoint("TASK-CHAOS-5", "claim", log=log)
        record_checkpoint("TASK-CHAOS-5", "handler", log=log)
        record_checkpoint("TASK-CHAOS-5", "submit", log=log)
        # Crash after 'submit', before 'event'.
        assert resume_step("TASK-CHAOS-5", log) == "event"


def test_chaos_6_committed_poisoned_state_recovery() -> None:
    """A task's committed output is later found to be poisoned (e.g. a
    corrupted canonical write). It must be dead-lettered with a policy
    that does NOT silently return it to normal dispatch -- recovery
    requires a repair task or operator decision, matching Gap-Register
    Bucket 3.2 ("recovery from a committed poisoned state" -- previously
    entirely untested).
    """
    with tempfile.TemporaryDirectory() as tmp:
        queue_log = Path(tmp) / "dead_letters.jsonl"
        event_log = Path(tmp) / "events.jsonl"

        dl_id = enqueue(
            "TASK-CHAOS-6", "some-agent", reason="poisoned_state",
            replay_policy="create_repair_task",
            queue_log=queue_log, event_log=event_log,
        )

        result = replay(dl_id, queue_log=queue_log, event_log=event_log)
        assert result["replay_status"] == "blocked", (
            "poisoned-state replay via create_repair_task must NOT silently "
            "requeue to READY -- it must block pending a real repair task"
        )

        # A second replay attempt on an already-terminal record must refuse.
        try:
            replay(dl_id, queue_log=queue_log, event_log=event_log)
            raise AssertionError("expected DeadLetterError on re-replaying a blocked record")
        except DeadLetterError:
            pass


def main() -> int:
    tests = [
        test_chaos_1_killed_handler_mid_task,
        test_chaos_2_stale_mirror_detected,
        test_chaos_3_malformed_protocol_output_detected,
        test_chaos_4_hung_agent_reaper_path,
        test_chaos_5_mid_task_resume_after_multiple_completed_steps,
        test_chaos_6_committed_poisoned_state_recovery,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
