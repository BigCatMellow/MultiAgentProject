#!/usr/bin/env python3
"""Tests for durable halt state and dispatch claim gates."""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.db.claims import claim_task_with_reason  # noqa: E402
from MAP_System.scripts.agent_loop import Config, claim_node  # noqa: E402
from MAP_System.scripts.halt_state import (  # noqa: E402
    HaltStateError,
    clear_halt,
    dispatch_block_reason_for_task,
    load_halt_state,
    set_halt,
)


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript((ROOT / "migration" / "schema.sql").read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES ('codex-lab-test', 'Codex Test', 'core', 'available')"
        )
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES ('command-center', 'Command Center', 'system', 'available')"
        )
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status, owner, attempt, max_attempts)
            VALUES ('TASK-I', 'TEST', 'Implement feature', 'Paid core work.', 'implementation', 'implementer', 'READY', 'command-center', 0, 3)
            """
        )
        conn.execute(
            "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES ('TASK-I', 'feature works')"
        )


def test_paid_halt_blocks_paid_lane_and_allows_review_lane() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt.json"
        record = set_halt(
            state="halt_paid_dispatch",
            reason="spend_rate_breaker",
            set_by="codex-lab-test",
            scope="paid",
            clear_requires="objective_evidence",
            path=halt_path,
        )

        assert record["state"] == "halt_paid_dispatch"
        assert dispatch_block_reason_for_task(
            {"task_id": "TASK-I", "task_type": "implementation", "role": "implementer"},
            record,
        ) == "halt_paid_dispatch"
        assert dispatch_block_reason_for_task(
            {"task_id": "TASK-R", "task_type": "review", "role": "reviewer"},
            record,
        ) is None


def test_clear_authority_rejects_helper_and_allows_core_when_policy_allows() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt.json"
        set_halt(
            state="halt_paid_dispatch",
            reason="spend_rate_breaker",
            set_by="cost-governance",
            scope="paid",
            clear_requires="objective_evidence",
            path=halt_path,
        )

        try:
            clear_halt(cleared_by="task151review-vida", clear_reason="helper should not clear", path=halt_path)
        except HaltStateError as exc:
            assert "not authorized" in str(exc)
        else:  # pragma: no cover - defensive failure path
            raise AssertionError("helper clear unexpectedly succeeded")

        cleared = clear_halt(
            cleared_by="codex-lab-test",
            clear_reason="objective evidence shows paid dispatch disabled",
            path=halt_path,
        )
        assert cleared["state"] == "clear"
        assert cleared["cleared_by"] == "codex-lab-test"


def test_global_clear_requires_command_center() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt.json"
        set_halt(
            state="halt_all_dispatch",
            reason="operator_stop",
            set_by="command-center",
            scope="global",
            clear_requires="command_center",
            path=halt_path,
        )

        try:
            clear_halt(cleared_by="codex-lab-test", clear_reason="not enough authority", path=halt_path)
        except HaltStateError as exc:
            assert "not authorized" in str(exc)
        else:  # pragma: no cover - defensive failure path
            raise AssertionError("core global clear unexpectedly succeeded")

        cleared = clear_halt(
            cleared_by="command-center",
            clear_reason="operator explicitly cleared global halt",
            path=halt_path,
        )
        assert cleared["state"] == "clear"


def test_validator_global_halt_clear_requires_command_center() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt.json"
        set_halt(
            state="halt_all_dispatch",
            reason="validator_blocking_anomaly",
            set_by="validator",
            scope="global",
            clear_requires="command_center",
            path=halt_path,
        )

        try:
            clear_halt(cleared_by="validator", clear_reason="validator self-clear", path=halt_path)
        except HaltStateError as exc:
            assert "not authorized" in str(exc)
        else:  # pragma: no cover - defensive failure path
            raise AssertionError("validator global halt clear unexpectedly succeeded")

        cleared = clear_halt(
            cleared_by="command-center",
            clear_reason="structural validator halt adjudicated by command-center",
            path=halt_path,
        )
        assert cleared["state"] == "clear"
        assert cleared["cleared_by"] == "command-center"


def test_claim_gate_blocks_paid_task_under_halt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        halt_path = Path(tmp) / "halt.json"
        init_db(db)
        set_halt(
            state="halt_paid_dispatch",
            reason="spend_rate_breaker",
            set_by="cost-governance",
            scope="paid",
            path=halt_path,
        )
        old_path = os.environ.get("MAP_HALT_STATE_PATH")
        os.environ["MAP_HALT_STATE_PATH"] = str(halt_path)
        try:
            claimed, reason = claim_task_with_reason("TASK-I", "codex-lab-test", db_path=db)
        finally:
            if old_path is None:
                os.environ.pop("MAP_HALT_STATE_PATH", None)
            else:
                os.environ["MAP_HALT_STATE_PATH"] = old_path

        assert not claimed
        assert reason == "halt_paid_dispatch"


def test_agent_loop_claim_node_reports_halt_reason() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        halt_path = Path(tmp) / "halt.json"
        init_db(db)
        set_halt(
            state="halt_paid_dispatch",
            reason="spend_rate_breaker",
            set_by="cost-governance",
            scope="paid",
            path=halt_path,
        )
        old_path = os.environ.get("MAP_HALT_STATE_PATH")
        os.environ["MAP_HALT_STATE_PATH"] = str(halt_path)
        try:
            config = Config(
                agent_id="codex-lab-test",
                db_path=db,
                once=True,
                dry_run=False,
                handler=None,
                heartbeat_interval=300,
                lease_seconds=1800,
                export_after_submit=False,
                max_iterations=1,
                retry_cooldown=0,
            )
            result = claim_node({"ready_tasks": ["TASK-I"], "attempt_count": 0}, config)
        finally:
            if old_path is None:
                os.environ.pop("MAP_HALT_STATE_PATH", None)
            else:
                os.environ["MAP_HALT_STATE_PATH"] = old_path

        assert result["last_result"] == "claim_blocked_by_halt_paid_dispatch"


def test_missing_halt_file_loads_clear_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        record = load_halt_state(Path(tmp) / "missing.json")
        assert record["state"] == "clear"


def main() -> int:
    tests = [
        test_paid_halt_blocks_paid_lane_and_allows_review_lane,
        test_clear_authority_rejects_helper_and_allows_core_when_policy_allows,
        test_global_clear_requires_command_center,
        test_validator_global_halt_clear_requires_command_center,
        test_claim_gate_blocks_paid_task_under_halt,
        test_agent_loop_claim_node_reports_halt_reason,
        test_missing_halt_file_loads_clear_record,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
