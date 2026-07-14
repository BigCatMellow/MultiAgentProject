#!/usr/bin/env python3
"""Idempotency registry and failure circuit breaker (TASK-161, from
map-resilience-controls-spec.md).

Circuit-breaker escalation to repair_only/global_halt reuses TASK-159's
halt_state.py store -- per this task's own description, no parallel halt
table is created. scoped_pause/warn/accounting_only states are lighter-
weight and stored locally, since the kill-switch store's vocabulary
(clear/halt_paid_dispatch/halt_all_dispatch/repair_only) has no room for a
per-agent "temporarily pause this one lane, nothing else" concept beyond
repair_only+scope=agent.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent

import sys
sys.path.insert(0, str(REPO))
from MAP_System.scripts.halt_state import set_halt  # noqa: E402

DEFAULT_IDEMPOTENCY_LOG = ROOT / "shared" / "idempotency-registry.jsonl"
DEFAULT_BREAKER_LOG = ROOT / "shared" / "breaker-signals.jsonl"

VALID_IDEMPOTENCY_STATUSES = {"started", "applied", "duplicate_ignored", "conflict", "failed"}
VALID_BREAKER_INPUTS = {
    "agent_repeated_stale", "agent_handler_failure_rate", "subsystem_validator_failures",
    "dead_letter_volume", "poisoned_state_detected", "local_model_unhealthy",
}
VALID_BREAKER_STATES = ("accounting_only", "warn", "scoped_pause", "repair_only", "global_halt")


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def content_hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:16]


class IdempotencyConflict(RuntimeError):
    """Raised when the same key is reused with a different request payload."""


def _read_registry(log: Path) -> list[dict]:
    if not log.exists():
        return []
    return [json.loads(l) for l in log.read_text(encoding="utf-8").splitlines() if l.strip()]


def _latest_for_key(log: Path, idempotency_key: str) -> dict | None:
    matches = [r for r in _read_registry(log) if r["idempotency_key"] == idempotency_key]
    return matches[-1] if matches else None


def check_and_record(
    idempotency_key: str,
    operation: str,
    target: str,
    writer_id: str,
    request_payload: object,
    *,
    log: Path = DEFAULT_IDEMPOTENCY_LOG,
) -> dict:
    """Implements the spec's retry rules:
    - same key + same request hash + already applied -> return prior result
      (status=duplicate_ignored), do not write again.
    - same key + same request hash + still started -> return the existing
      in-progress record as-is (an in-progress duplicate, per the spec's
      resume/checkpoint policy), not a fresh started intent.
    - same key + different request hash, for EITHER started or applied ->
      conflict, do not guess intent. (TASK-161 review finding: the
      original implementation only checked this for applied records, so a
      still-started record could be silently reused for different
      semantic content -- an isolated probe reproduced two started
      records for one key with different hashes before this fix.)
    - a prior `failed` record does not block a fresh attempt (failure
      means the original intent did not succeed; a corrected/different
      payload on retry is expected, not a conflict).
    - unseen key -> started (caller performs the write, then calls
      mark_applied()).
    """
    request_hash = content_hash(request_payload)
    existing = _latest_for_key(log, idempotency_key)

    if existing is not None and existing["status"] in ("applied", "started"):
        if existing["request_hash"] == request_hash:
            if existing["status"] == "applied":
                record = {**existing, "status": "duplicate_ignored", "last_seen_at": _now_iso()}
                _append(log, record)
                return record
            record = {**existing, "last_seen_at": _now_iso()}
            _append(log, record)
            return record
        raise IdempotencyConflict(
            f"{idempotency_key} already {existing['status']} with a different request "
            f"(hash {existing['request_hash']} != {request_hash})"
        )

    record = {
        "idempotency_key": idempotency_key,
        "operation": operation,
        "target": target,
        "writer_id": writer_id,
        "request_hash": request_hash,
        "result_hash": None,
        "status": "started",
        "created_at": (existing or {}).get("created_at", _now_iso()),
        "last_seen_at": _now_iso(),
        "related_event_ids": [],
    }
    _append(log, record)
    return record


def mark_applied(idempotency_key: str, result_payload: object, *, log: Path = DEFAULT_IDEMPOTENCY_LOG) -> dict:
    existing = _latest_for_key(log, idempotency_key)
    if existing is None:
        raise IdempotencyConflict(f"no started record for {idempotency_key}")
    record = {
        **existing,
        "status": "applied",
        "result_hash": content_hash(result_payload),
        "last_seen_at": _now_iso(),
    }
    _append(log, record)
    return record


def mark_failed(idempotency_key: str, *, log: Path = DEFAULT_IDEMPOTENCY_LOG) -> dict:
    existing = _latest_for_key(log, idempotency_key)
    if existing is None:
        raise IdempotencyConflict(f"no started record for {idempotency_key}")
    record = {**existing, "status": "failed", "last_seen_at": _now_iso()}
    _append(log, record)
    return record


def _append(log: Path, record: dict) -> None:
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def record_breaker_signal(
    input_type: str,
    scope_target: str,
    *,
    log: Path = DEFAULT_BREAKER_LOG,
) -> dict:
    if input_type not in VALID_BREAKER_INPUTS:
        raise ValueError(f"invalid breaker input: {input_type}")
    record = {"input_type": input_type, "scope_target": scope_target, "recorded_at": _now_iso()}
    _append(log, record)
    return record


def evaluate_breaker_state(
    input_type: str,
    scope_target: str,
    *,
    log: Path = DEFAULT_BREAKER_LOG,
    window: int = 10,
    scoped_pause_threshold: int = 2,
    repair_only_threshold: int = 4,
) -> str:
    """Grades recent signal volume for one (input_type, scope_target) pair
    into a breaker state. This is a simple threshold model, not the full
    calibrated policy real production use would need (see
    map-real-parameter-calibration.md) -- it exists so a breaker state is
    computable and testable today, with thresholds a future task can tune
    against real incident data.
    """
    if input_type not in VALID_BREAKER_INPUTS:
        raise ValueError(f"invalid breaker input: {input_type}")
    records = [
        r for r in _read_registry(log)[-window:]
        if r["input_type"] == input_type and r["scope_target"] == scope_target
    ]
    count = len(records)
    if count == 0:
        return "accounting_only"
    if count < scoped_pause_threshold:
        return "warn"
    if count < repair_only_threshold:
        return "scoped_pause"
    return "repair_only"


def apply_breaker_state(
    state: str,
    scope_target: str,
    *,
    set_by: str = "resilience-controls",
    halt_path: str | None = None,
) -> str | None:
    """Escalates scoped_pause/repair_only into TASK-159's shared halt
    store (never a parallel table); accounting_only/warn stay local
    (breaker-signals.jsonl + mission-control attention item), matching the
    spec's dispatch-behavior table.
    """
    if state not in VALID_BREAKER_STATES:
        raise ValueError(f"invalid breaker state: {state}")
    if state in ("accounting_only", "warn"):
        return None
    if state == "global_halt":
        record = set_halt(
            state="halt_all_dispatch", reason="validator_blocking_anomaly",
            set_by=set_by, scope="global", path=halt_path,
        )
        return record["halt_id"]
    # scoped_pause and repair_only both map to the halt store's repair_only
    # state, scoped to the affected agent/subsystem -- distinct dispatch
    # meanings (spec: scoped_pause blocks only that lane; repair_only
    # additionally allows only review/repair for that scope), but
    # halt_state.py's dispatch_block_reason_for_task already treats
    # repair_only as "review/repair/operator only" for anything in scope,
    # which correctly covers both.
    record = set_halt(
        state="repair_only", reason="validator_blocking_anomaly",
        set_by=set_by, scope="agent", target=scope_target, path=halt_path,
    )
    return record["halt_id"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    signal_cmd = sub.add_parser("signal")
    signal_cmd.add_argument("input_type", choices=sorted(VALID_BREAKER_INPUTS))
    signal_cmd.add_argument("scope_target")

    evaluate_cmd = sub.add_parser("evaluate")
    evaluate_cmd.add_argument("input_type", choices=sorted(VALID_BREAKER_INPUTS))
    evaluate_cmd.add_argument("scope_target")

    args = parser.parse_args()
    if args.command == "signal":
        print(record_breaker_signal(args.input_type, args.scope_target))
    else:
        print(evaluate_breaker_state(args.input_type, args.scope_target))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
