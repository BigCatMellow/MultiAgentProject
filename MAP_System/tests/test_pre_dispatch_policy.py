#!/usr/bin/env python3
"""Tests for TASK-163 pre-dispatch policy checker and claim gate."""

from __future__ import annotations

import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.db.claims import claim_task_with_reason  # noqa: E402
from MAP_System.scripts.pre_dispatch_policy import evaluate_pre_dispatch, load_task_from_db  # noqa: E402


def base_task(**overrides):
    task = {
        "task_id": "TASK-P",
        "title": "Safe architecture spec",
        "description": "Implement a bounded architecture spec inside approved scope.",
        "task_type": "implementation",
        "role": "engineer",
        "output_paths": ["MAP_System/scripts/example.py"],
        "acceptance_criteria": ["works"],
    }
    task.update(overrides)
    return task


def core_result(task):
    return evaluate_pre_dispatch(task, "codex-lab-test", worker_tier=1)


def test_core_destructive_action_requires_command_center_approval() -> None:
    result = core_result(base_task(destructive_action=True))
    assert result["decision"] == "require_approval"
    assert result["approval_authority"] == "command-center"
    assert "REQUIRE_CORE_DESTRUCTIVE_APPROVAL" in result["reasons"]
    assert "operator instruction or approving decision" in result["required_evidence"]


def test_core_authority_policy_decision_requires_command_center_approval() -> None:
    for decision_class in ("AUTHORITY", "POLICY"):
        result = core_result(base_task(decision_class=decision_class))
        assert result["decision"] == "require_approval"
        assert result["approval_authority"] == "command-center"
        assert "REQUIRE_COMMAND_CENTER_DECISION" in result["reasons"]


def test_security_or_structural_risk_requires_approval() -> None:
    result = core_result(base_task(risk_class="SECURITY"))
    assert result["decision"] == "require_approval"
    assert "REQUIRE_SECURITY_STRUCTURAL_APPROVAL" in result["reasons"]

    result = core_result(base_task(risk_severity="STRUCTURAL"))
    assert result["decision"] == "require_approval"
    assert "REQUIRE_SECURITY_STRUCTURAL_APPROVAL" in result["reasons"]


def test_unknown_risk_trust_boundary_requires_approval() -> None:
    result = core_result(base_task(trust_boundary_crossing=True))
    assert result["decision"] == "require_approval"
    assert "REQUIRE_UNKNOWN_TRUST_BOUNDARY_APPROVAL" in result["reasons"]
    assert "risk classification" in result["required_evidence"]


def test_safe_core_architecture_documentation_is_allowed() -> None:
    result = core_result(base_task(task_type="architecture", decision_class="ARCHITECTURE"))
    assert result["decision"] == "allow"
    assert result["reasons"] == ["ALLOW_WITHIN_TIER"]


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript((ROOT / "migration" / "schema.sql").read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES ('codex-lab-test', 'Codex Test', 'core', 'available')"
        )


def insert_task(path: Path, *, description: str, output_path: str = "MAP_System/scripts/example.py") -> None:
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status, owner, attempt, max_attempts)
            VALUES ('TASK-P', 'TEST', 'Policy-gated task', ?, 'implementation', 'engineer', 'READY', 'command-center', 0, 3)
            """,
            (description,),
        )
        conn.execute("INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES ('TASK-P', 'works')")
        conn.execute("INSERT INTO task_output_paths (task_id, path) VALUES ('TASK-P', ?)", (output_path,))


def test_db_loader_includes_output_paths_and_criteria() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db)
        insert_task(db, description="Safe work")

        task = load_task_from_db("TASK-P", db)
        assert task["output_paths"] == ["MAP_System/scripts/example.py"]
        assert task["acceptance_criteria"] == ["works"]


def test_claim_gate_blocks_policy_required_approval_before_claim() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "map.db"
        init_db(db)
        insert_task(db, description="Run force push cleanup. force push")

        claimed, reason = claim_task_with_reason("TASK-P", "codex-lab-test", db_path=db)

        assert not claimed
        assert reason is not None
        assert reason.startswith("policy_require_approval:")
        assert "REQUIRE_CORE_DESTRUCTIVE_APPROVAL" in reason
        with sqlite3.connect(db) as conn:
            row = conn.execute("SELECT status, claimed_by FROM tasks WHERE task_id='TASK-P'").fetchone()
        assert row == ("READY", None)


def main() -> int:
    tests = [
        test_core_destructive_action_requires_command_center_approval,
        test_core_authority_policy_decision_requires_command_center_approval,
        test_security_or_structural_risk_requires_approval,
        test_unknown_risk_trust_boundary_requires_approval,
        test_safe_core_architecture_documentation_is_allowed,
        test_db_loader_includes_output_paths_and_criteria,
        test_claim_gate_blocks_policy_required_approval_before_claim,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
