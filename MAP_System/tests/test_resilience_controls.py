#!/usr/bin/env python3
"""Tests for the idempotency registry and failure circuit breaker (TASK-161)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.resilience_controls import (  # noqa: E402
    check_and_record,
    mark_applied,
    mark_failed,
    IdempotencyConflict,
    record_breaker_signal,
    evaluate_breaker_state,
    apply_breaker_state,
)
from MAP_System.scripts.halt_state import load_halt_state  # noqa: E402
from MAP_System.scripts.dead_letter_queue import (  # noqa: E402
    enqueue,
    replay,
    queue_depth,
    DeadLetterError,
)


def test_first_attempt_starts_then_applies() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "idempotency.jsonl"
        started = check_and_record("K1", "submit_task", "TASK-1", "agent-a", {"foo": "bar"}, log=log)
        assert started["status"] == "started"
        applied = mark_applied("K1", {"result": "ok"}, log=log)
        assert applied["status"] == "applied"


def test_same_key_same_payload_after_applied_is_duplicate_ignored() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "idempotency.jsonl"
        check_and_record("K2", "submit_task", "TASK-2", "agent-a", {"foo": "bar"}, log=log)
        mark_applied("K2", {"result": "ok"}, log=log)

        retry = check_and_record("K2", "submit_task", "TASK-2", "agent-a", {"foo": "bar"}, log=log)
        assert retry["status"] == "duplicate_ignored"


def test_same_key_different_payload_after_applied_is_conflict() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "idempotency.jsonl"
        check_and_record("K3", "submit_task", "TASK-3", "agent-a", {"foo": "bar"}, log=log)
        mark_applied("K3", {"result": "ok"}, log=log)

        try:
            check_and_record("K3", "submit_task", "TASK-3", "agent-a", {"foo": "DIFFERENT"}, log=log)
            raise AssertionError("expected IdempotencyConflict")
        except IdempotencyConflict:
            pass


def test_same_key_different_payload_while_still_started_is_conflict() -> None:
    """TASK-161 review finding: the original implementation only checked
    for a hash mismatch when the prior record was 'applied' -- a still-
    'started' record could be silently reused for different semantic
    content, producing two started records for one key with no conflict.
    """
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "idempotency.jsonl"
        check_and_record("K5", "submit_task", "TASK-5", "agent-a", {"foo": "bar"}, log=log)
        # K5 is still 'started' -- never applied or failed.
        try:
            check_and_record("K5", "submit_task", "TASK-5", "agent-a", {"foo": "DIFFERENT"}, log=log)
            raise AssertionError("expected IdempotencyConflict for started+different payload")
        except IdempotencyConflict:
            pass


def test_same_key_same_payload_while_still_started_returns_existing_record() -> None:
    """A retry of the exact same intent while the first attempt is still
    in-flight (e.g. a network retry before the first response lands) must
    return the existing started record, not create a second independent
    'started' entry for the same key.
    """
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "idempotency.jsonl"
        first = check_and_record("K6", "submit_task", "TASK-6", "agent-a", {"foo": "bar"}, log=log)
        retry = check_and_record("K6", "submit_task", "TASK-6", "agent-a", {"foo": "bar"}, log=log)
        assert retry["status"] == "started"
        assert retry["request_hash"] == first["request_hash"]


def test_mark_failed_allows_a_later_retry_to_start_fresh() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "idempotency.jsonl"
        check_and_record("K4", "export_to_files", "TASK-4", "agent-a", {"x": 1}, log=log)
        mark_failed("K4", log=log)

        retry = check_and_record("K4", "export_to_files", "TASK-4", "agent-a", {"x": 1}, log=log)
        assert retry["status"] == "started"


def test_breaker_state_escalates_with_signal_volume() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "breakers.jsonl"
        assert evaluate_breaker_state("agent_repeated_stale", "agent-x", log=log) == "accounting_only"

        record_breaker_signal("agent_repeated_stale", "agent-x", log=log)
        assert evaluate_breaker_state("agent_repeated_stale", "agent-x", log=log) == "warn"

        record_breaker_signal("agent_repeated_stale", "agent-x", log=log)
        assert evaluate_breaker_state("agent_repeated_stale", "agent-x", log=log) == "scoped_pause"

        record_breaker_signal("agent_repeated_stale", "agent-x", log=log)
        record_breaker_signal("agent_repeated_stale", "agent-x", log=log)
        assert evaluate_breaker_state("agent_repeated_stale", "agent-x", log=log) == "repair_only"


def test_breaker_signals_are_scoped_per_target() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "breakers.jsonl"
        for _ in range(4):
            record_breaker_signal("agent_repeated_stale", "agent-x", log=log)
        assert evaluate_breaker_state("agent_repeated_stale", "agent-x", log=log) == "repair_only"
        # A different agent's signal history is untouched.
        assert evaluate_breaker_state("agent_repeated_stale", "agent-y", log=log) == "accounting_only"


def test_apply_breaker_state_accounting_only_and_warn_never_touch_halt_store() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt-state.json"
        assert apply_breaker_state("accounting_only", "agent-x", halt_path=str(halt_path)) is None
        assert apply_breaker_state("warn", "agent-x", halt_path=str(halt_path)) is None
        assert not halt_path.exists()


def test_apply_breaker_state_scoped_pause_and_repair_only_use_shared_halt_store() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt-state.json"
        halt_id = apply_breaker_state(
            "scoped_pause", "agent-x", set_by="validator-breaker", halt_path=str(halt_path),
        )
        assert halt_id is not None
        record = load_halt_state(str(halt_path))
        assert record["state"] == "repair_only"
        assert record["scope"] == "agent"
        assert record["target"] == "agent-x"


def test_apply_breaker_state_global_halt_uses_shared_halt_store() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt-state.json"
        halt_id = apply_breaker_state(
            "global_halt", "system", set_by="validator-breaker", halt_path=str(halt_path),
        )
        assert halt_id is not None
        record = load_halt_state(str(halt_path))
        assert record["state"] == "halt_all_dispatch"
        assert record["scope"] == "global"


def test_no_second_halt_table_is_created() -> None:
    import inspect
    import MAP_System.scripts.resilience_controls as rc

    source = inspect.getsource(rc)
    assert "from MAP_System.scripts.halt_state import set_halt" in source
    assert "CREATE TABLE" not in source


def test_dead_letter_enqueue_rejects_invalid_reason() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        queue_log = Path(tmp) / "dlq.jsonl"
        event_log = Path(tmp) / "events.jsonl"
        try:
            enqueue("TASK-X", "agent-a", reason="not_a_real_reason", queue_log=queue_log, event_log=event_log)
            raise AssertionError("expected DeadLetterError")
        except DeadLetterError:
            pass


def test_dead_letter_replay_close_unreplayable() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        queue_log = Path(tmp) / "dlq.jsonl"
        event_log = Path(tmp) / "events.jsonl"
        dl_id = enqueue(
            "TASK-Y", "agent-a", reason="manual_quarantine",
            replay_policy="close_unreplayable", queue_log=queue_log, event_log=event_log,
        )
        result = replay(dl_id, queue_log=queue_log, event_log=event_log)
        assert result["replay_status"] == "closed"


def test_queue_depth_counts_only_still_queued_records() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        queue_log = Path(tmp) / "dlq.jsonl"
        event_log = Path(tmp) / "events.jsonl"
        enqueue("TASK-A", "a", reason="handler_crash", queue_log=queue_log, event_log=event_log)
        dl_id = enqueue("TASK-B", "a", reason="handler_crash", replay_policy="close_unreplayable", queue_log=queue_log, event_log=event_log)
        assert queue_depth("handler_crash", queue_log=queue_log) == 2

        replay(dl_id, queue_log=queue_log, event_log=event_log)
        assert queue_depth("handler_crash", queue_log=queue_log) == 1


def main() -> int:
    tests = [
        test_first_attempt_starts_then_applies,
        test_same_key_same_payload_after_applied_is_duplicate_ignored,
        test_same_key_different_payload_after_applied_is_conflict,
        test_same_key_different_payload_while_still_started_is_conflict,
        test_same_key_same_payload_while_still_started_returns_existing_record,
        test_mark_failed_allows_a_later_retry_to_start_fresh,
        test_breaker_state_escalates_with_signal_volume,
        test_breaker_signals_are_scoped_per_target,
        test_apply_breaker_state_accounting_only_and_warn_never_touch_halt_store,
        test_apply_breaker_state_scoped_pause_and_repair_only_use_shared_halt_store,
        test_apply_breaker_state_global_halt_uses_shared_halt_store,
        test_no_second_halt_table_is_created,
        test_dead_letter_enqueue_rejects_invalid_reason,
        test_dead_letter_replay_close_unreplayable,
        test_queue_depth_counts_only_still_queued_records,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
