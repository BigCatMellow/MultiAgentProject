#!/usr/bin/env python3
"""Canonical MAP dead-letter queue (TASK-161, from map-resilience-controls-spec.md).

Append-only JSONL store under MAP_System/dead_letters/. Every record needs
replay or closure instructions -- this is not a trash folder. Replay always
goes through sanctioned task transitions (db/claims.py), never a manual
task_graph.json edit.

Consolidates TASK-158's interim dead-letter mechanism in
scripts/liveness_reaper.py (dead_letter_task/replay_dead_letter), which was
explicitly documented there as needing to fold into this canonical queue
once it existed. liveness_reaper.py's own dead-letter functions remain for
backward compatibility (any code already calling them keeps working) but
new callers should use this module.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

try:
    from MAP_System.scripts.event_trace import add_trace_fields
except ModuleNotFoundError:  # direct script execution
    from event_trace import add_trace_fields

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
DEFAULT_DB = ROOT / "map.db"
DEFAULT_QUEUE_LOG = ROOT / "dead_letters" / "dead_letters.jsonl"
DEFAULT_EVENT_LOG = ROOT / "events" / "events.jsonl"

VALID_REASONS = {
    "handler_crash", "lease_reclaimed", "repeated_failure",
    "poisoned_state", "validator_halt", "manual_quarantine",
}
VALID_REPLAY_POLICIES = {
    "return_ready", "resume_from_checkpoint", "create_repair_task",
    "operator_decision", "close_unreplayable",
}
VALID_REPLAY_STATUSES = {"queued", "replayed", "closed", "blocked"}
REPLAYABLE_TASK_STATUSES = {"IN_PROGRESS", "READY"}


class DeadLetterError(RuntimeError):
    """Raised on invalid enqueue/replay input or an unsafe replay attempt."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _append_event(
    event_type: str,
    summary: str,
    task_id: str,
    action: str,
    target: str,
    artifact_paths: list[str] | None = None,
    event_log: Path = DEFAULT_EVENT_LOG,
) -> None:
    event = {
        "created_at": _now_iso(),
        "type": event_type,
        "task_id": task_id,
        "sender": "dead-letter-queue",
        "summary": summary,
        "artifact_paths": artifact_paths or [],
        "actor": "dead-letter-queue",
        "action": action,
        "target": target,
    }
    add_trace_fields(event, actor="dead-letter-queue", action=action, target=target)
    with open(event_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _read_records(queue_log: Path) -> list[dict]:
    if not queue_log.exists():
        return []
    return [json.loads(l) for l in queue_log.read_text(encoding="utf-8").splitlines() if l.strip()]


def _latest_record(queue_log: Path, dead_letter_id: str) -> dict | None:
    matches = [r for r in _read_records(queue_log) if r["dead_letter_id"] == dead_letter_id]
    return matches[-1] if matches else None


def enqueue(
    task_id: str,
    agent_id: str,
    reason: str,
    *,
    attempt_count: int = 1,
    last_checkpoint_id: str | None = None,
    artifact_paths: list[str] | None = None,
    idempotency_keys: list[str] | None = None,
    replay_policy: str = "return_ready",
    queue_log: Path = DEFAULT_QUEUE_LOG,
    event_log: Path = DEFAULT_EVENT_LOG,
) -> str:
    """Append a dead-letter record. Fails loudly on an invalid reason or
    replay_policy rather than silently accepting free-text values that
    downstream consumers (mission-control, replay tooling) won't recognize.
    """
    if reason not in VALID_REASONS:
        raise DeadLetterError(f"invalid reason: {reason} (must be one of {sorted(VALID_REASONS)})")
    if replay_policy not in VALID_REPLAY_POLICIES:
        raise DeadLetterError(f"invalid replay_policy: {replay_policy}")

    queue_log.parent.mkdir(parents=True, exist_ok=True)
    dead_letter_id = f"DLQ-{uuid.uuid4().hex[:8]}"
    record = {
        "dead_letter_id": dead_letter_id,
        "task_id": task_id,
        "agent_id": agent_id,
        "detected_at": _now_iso(),
        "reason": reason,
        "attempt_count": attempt_count,
        "last_checkpoint_id": last_checkpoint_id,
        "artifact_paths": artifact_paths or [],
        "idempotency_keys": idempotency_keys or [],
        "replay_policy": replay_policy,
        "replay_status": "queued",
    }
    with open(queue_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    _append_event(
        "PROGRESS",
        f"Dead-lettered {task_id} (agent {agent_id}, reason={reason}, policy={replay_policy})",
        task_id=task_id, action="enqueue", target=dead_letter_id,
        artifact_paths=[str(queue_log.relative_to(REPO))] if queue_log.is_relative_to(REPO) else [str(queue_log)],
        event_log=event_log,
    )
    return dead_letter_id


def _export_and_validate_mirrors(db_path: Path | None, mirror_root: Path | None) -> None:
    export_cmd = [sys.executable, str(ROOT / "migration" / "export_to_files.py")]
    validate_cmd = [sys.executable, str(ROOT / "scripts" / "validate_task_mirrors.py")]
    if db_path is not None:
        export_cmd += ["--db", str(db_path)]
        validate_cmd += ["--db", str(db_path)]
    if mirror_root is not None:
        export_cmd += ["--output-dir", str(mirror_root)]
        validate_cmd += ["--root", str(mirror_root)]
    export = subprocess.run(export_cmd, cwd=REPO, text=True, capture_output=True, check=False)
    if export.returncode != 0:
        raise DeadLetterError(f"export_to_files.py failed: {export.stderr.strip()}")
    validate = subprocess.run(validate_cmd, cwd=REPO, text=True, capture_output=True, check=False)
    if validate.returncode != 0:
        raise DeadLetterError(f"validate_task_mirrors.py failed after replay: {validate.stdout.strip()}")


def replay(
    dead_letter_id: str,
    *,
    queue_log: Path = DEFAULT_QUEUE_LOG,
    db_path: Path = DEFAULT_DB,
    mirror_root: Path | None = None,
    event_log: Path = DEFAULT_EVENT_LOG,
) -> dict:
    """Replay per the record's replay_policy. Only `return_ready` is
    executed as a real state transition here (requeue to READY, mirroring
    liveness_reaper's replay path); `resume_from_checkpoint` defers to
    durable_execution.py (a different task's step, not duplicated here);
    `create_repair_task`/`operator_decision` are closed with `blocked`
    status and a note, since they require human/decomposer action this
    queue does not perform; `close_unreplayable` simply closes the record.
    """
    record = _latest_record(queue_log, dead_letter_id)
    if record is None:
        raise DeadLetterError(f"unknown dead_letter_id: {dead_letter_id}")
    if record["replay_status"] in {"replayed", "closed", "blocked"}:
        raise DeadLetterError(
            f"{dead_letter_id} is already {record['replay_status']} -- "
            "blocked records require a human/decomposer action (repair task "
            "or operator decision), not another automated replay() call"
        )

    policy = record["replay_policy"]
    task_id = record["task_id"]

    if policy == "return_ready":
        conn = sqlite3.connect(db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            row = conn.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
            if row is None:
                raise DeadLetterError(f"{task_id} not found in tasks table")
            status = row[0]
            if status not in REPLAYABLE_TASK_STATUSES:
                raise DeadLetterError(f"{task_id} is {status}, not replayable via return_ready")
            if status == "IN_PROGRESS":
                conn.execute(
                    """
                    UPDATE tasks SET status = 'READY', claimed_by = NULL,
                        lease_expires_at = NULL, heartbeat_at = NULL, updated_at = datetime('now')
                    WHERE task_id = ?
                    """,
                    (task_id,),
                )
                conn.commit()
        finally:
            conn.close()
        _export_and_validate_mirrors(db_path, mirror_root)
        new_status = "replayed"
    elif policy in {"create_repair_task", "operator_decision"}:
        new_status = "blocked"
    elif policy == "close_unreplayable":
        new_status = "closed"
    else:
        raise DeadLetterError(f"replay_policy {policy} requires a different subsystem (e.g. durable_execution.py)")

    updated = {**record, "replay_status": new_status, "replayed_at": _now_iso()}
    with open(queue_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(updated) + "\n")
    _append_event(
        "PROGRESS",
        f"Dead-letter {dead_letter_id} for {task_id} replayed via policy={policy} -> {new_status}",
        task_id=task_id, action="replay", target=dead_letter_id,
        event_log=event_log,
    )
    return updated


def queue_depth(reason: str | None = None, queue_log: Path = DEFAULT_QUEUE_LOG) -> int:
    """Latest-status-per-id count of still-queued records -- the
    dead_letter_volume circuit-breaker input from map-resilience-controls-spec.md.
    """
    latest_by_id: dict[str, dict] = {}
    for record in _read_records(queue_log):
        latest_by_id[record["dead_letter_id"]] = record
    queued = [r for r in latest_by_id.values() if r["replay_status"] == "queued"]
    if reason:
        queued = [r for r in queued if r["reason"] == reason]
    return len(queued)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    enqueue_cmd = sub.add_parser("enqueue")
    enqueue_cmd.add_argument("task_id")
    enqueue_cmd.add_argument("agent_id")
    enqueue_cmd.add_argument("--reason", required=True, choices=sorted(VALID_REASONS))
    enqueue_cmd.add_argument("--replay-policy", default="return_ready", choices=sorted(VALID_REPLAY_POLICIES))

    replay_cmd = sub.add_parser("replay")
    replay_cmd.add_argument("dead_letter_id")

    depth_cmd = sub.add_parser("depth")
    depth_cmd.add_argument("--reason", choices=sorted(VALID_REASONS))

    args = parser.parse_args()
    if args.command == "enqueue":
        result = enqueue(args.task_id, args.agent_id, args.reason, replay_policy=args.replay_policy)
        print(result)
    elif args.command == "replay":
        result = replay(args.dead_letter_id)
        print(json.dumps(result, indent=2))
    else:
        print(queue_depth(args.reason))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
