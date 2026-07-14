#!/usr/bin/env python3
"""Atomic SQLite task-claim helpers for MAP_System."""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from MAP_System.scripts.halt_state import dispatch_block_reason_for_task  # noqa: E402
from MAP_System.scripts.pre_dispatch_policy import evaluate_pre_dispatch  # noqa: E402

DEFAULT_DB = ROOT / "map.db"
DEFAULT_LEASE_SECONDS = 1800


class ClaimBlocked(RuntimeError):
    """Raised by claim_task_with_reason when a claim violates a MAP gate."""


def connect(db_path: str | Path = DEFAULT_DB) -> sqlite3.Connection:
    """Open the task-board database with foreign keys enabled."""
    path = Path(db_path)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _lease_modifier(lease_seconds: int) -> str:
    if lease_seconds <= 0:
        raise ValueError("lease_seconds must be positive")
    return f"+{int(lease_seconds)} seconds"


def _is_review_task(row: sqlite3.Row | tuple[str, str] | None) -> bool:
    if row is None:
        return False
    task_type = (row[0] or "").lower()
    role = (row[1] or "").lower()
    return task_type == "review" or role == "reviewer"


def claim_block_reason(
    task_id: str,
    agent_id: str,
    *,
    db_path: str | Path = DEFAULT_DB,
) -> str | None:
    """Return a human-readable claim gate failure reason, or None."""
    with connect(db_path) as conn:
        row = conn.execute(
            """
            SELECT task_id, project_id, title, description, task_type, role, owner
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()
        if row is None:
            return "unknown_task"

        task = {
            "task_id": row[0],
            "project_id": row[1],
            "title": row[2],
            "description": row[3],
            "task_type": row[4],
            "role": row[5],
        }
        dispatch_block = dispatch_block_reason_for_task(task)
        if dispatch_block:
            return dispatch_block

        review_row = (row[4], row[5])
        owner = row[6]
        if _is_review_task(review_row) and owner and owner.lower() == agent_id.lower():
            return "self_review"

        has_criteria = conn.execute(
            """
            SELECT 1
            FROM task_acceptance_criteria
            WHERE task_id = ?
              AND trim(criterion) != ''
            LIMIT 1
            """,
            (task_id,),
        ).fetchone()
        if not has_criteria:
            return "missing_acceptance_criteria"

        output_paths = [
            value
            for (value,) in conn.execute(
                "SELECT path FROM task_output_paths WHERE task_id = ? ORDER BY path",
                (task_id,),
            )
        ]
        acceptance_criteria = [
            value
            for (value,) in conn.execute(
                "SELECT criterion FROM task_acceptance_criteria WHERE task_id = ? ORDER BY id",
                (task_id,),
            )
        ]
        task["output_paths"] = output_paths
        task["acceptance_criteria"] = acceptance_criteria
        policy = evaluate_pre_dispatch(task, agent_id)
        if policy["decision"] != "allow":
            return f"policy_{policy['decision']}:{','.join(policy['reasons'])}"

    return None


def claim_task(
    task_id: str,
    agent_id: str,
    *,
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
    db_path: str | Path = DEFAULT_DB,
) -> bool:
    """Atomically claim a READY task or an expired in-progress task."""
    if claim_block_reason(task_id, agent_id, db_path=db_path):
        return False
    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET status = 'IN_PROGRESS',
                claimed_by = ?,
                lease_expires_at = datetime('now', ?),
                heartbeat_at = datetime('now'),
                attempt = attempt + 1,
                updated_at = datetime('now')
            WHERE task_id = ?
              AND (
                    status = 'READY'
                    OR (
                        status = 'IN_PROGRESS'
                        AND lease_expires_at IS NOT NULL
                        AND lease_expires_at < datetime('now')
                    )
                  )
              AND attempt < max_attempts
            """,
            (agent_id, _lease_modifier(lease_seconds), task_id),
        )
        return cursor.rowcount == 1


def claim_task_with_reason(
    task_id: str,
    agent_id: str,
    *,
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
    db_path: str | Path = DEFAULT_DB,
) -> tuple[bool, str | None]:
    """Claim a task and return a reason when a MAP claim gate blocks it."""
    reason = claim_block_reason(task_id, agent_id, db_path=db_path)
    if reason:
        return False, reason
    claimed = claim_task(task_id, agent_id, lease_seconds=lease_seconds, db_path=db_path)
    return claimed, None if claimed else "not_claimable"


def heartbeat(
    task_id: str,
    agent_id: str,
    *,
    lease_seconds: int = DEFAULT_LEASE_SECONDS,
    db_path: str | Path = DEFAULT_DB,
) -> bool:
    """Renew a lease for the agent that currently owns the claim."""
    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET heartbeat_at = datetime('now'),
                lease_expires_at = datetime('now', ?),
                updated_at = datetime('now')
            WHERE task_id = ?
              AND claimed_by = ?
              AND status = 'IN_PROGRESS'
            """,
            (_lease_modifier(lease_seconds), task_id, agent_id),
        )
        return cursor.rowcount == 1


def release_task(
    task_id: str,
    agent_id: str,
    *,
    status: str = "SUBMITTED",
    db_path: str | Path = DEFAULT_DB,
) -> bool:
    """Release a claimed task, clearing lease fields and setting a final status."""
    if not status:
        raise ValueError("status must not be empty")
    with connect(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE tasks
            SET status = ?,
                claimed_by = NULL,
                lease_expires_at = NULL,
                heartbeat_at = NULL,
                updated_at = datetime('now')
            WHERE task_id = ?
              AND claimed_by = ?
              AND status = 'IN_PROGRESS'
            """,
            (status, task_id, agent_id),
        )
        return cursor.rowcount == 1


def submit_task(
    task_id: str,
    agent_id: str,
    *,
    db_path: str | Path = DEFAULT_DB,
) -> bool:
    """Submit a claimed task for review."""
    return release_task(task_id, agent_id, status="SUBMITTED", db_path=db_path)


def expire_leases(*, db_path: str | Path = DEFAULT_DB) -> Sequence[str]:
    """Return expired in-progress claims to READY and return their task IDs."""
    with connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT task_id
            FROM tasks
            WHERE status = 'IN_PROGRESS'
              AND claimed_by IS NOT NULL
              AND lease_expires_at IS NOT NULL
              AND lease_expires_at < datetime('now')
            ORDER BY task_id
            """
        ).fetchall()
        task_ids = [row[0] for row in rows]
        if not task_ids:
            return []
        conn.executemany(
            """
            UPDATE tasks
            SET status = 'READY',
                claimed_by = NULL,
                lease_expires_at = NULL,
                heartbeat_at = NULL,
                updated_at = datetime('now')
            WHERE task_id = ?
            """,
            [(task_id,) for task_id in task_ids],
        )
        return task_ids
