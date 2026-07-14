#!/usr/bin/env python3
"""Tests for durable checkpoint/resume helpers (TASK-161)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.durable_execution import (  # noqa: E402
    record_checkpoint,
    get_last_checkpoint,
    resume_step,
    DurableExecutionError,
    STEP_ORDER,
)


def test_resume_step_starts_at_first_step_with_no_checkpoints() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "checkpoints.jsonl"
        assert resume_step("TASK-X", log) == STEP_ORDER[0]


def test_record_and_resume_progresses_through_steps() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "checkpoints.jsonl"
        record_checkpoint("TASK-X", "claim", log=log)
        assert resume_step("TASK-X", log) == "handler"

        record_checkpoint("TASK-X", "handler", log=log)
        assert resume_step("TASK-X", log) == "submit"

        record_checkpoint("TASK-X", "submit", log=log)
        record_checkpoint("TASK-X", "event", log=log)
        record_checkpoint("TASK-X", "export", log=log)
        assert resume_step("TASK-X", log) == "complete"


def test_recording_same_step_twice_in_a_row_is_rejected() -> None:
    """This is the double-apply guard: a killed-and-restarted process must
    not silently re-record (and thus re-apply) a step that already
    completed -- it should call resume_step() and continue forward instead.
    """
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "checkpoints.jsonl"
        record_checkpoint("TASK-X", "claim", log=log)
        try:
            record_checkpoint("TASK-X", "claim", log=log)
            raise AssertionError("expected DurableExecutionError on duplicate step")
        except DurableExecutionError:
            pass


def test_recording_an_earlier_step_after_a_later_one_is_rejected() -> None:
    """TASK-161 review finding: claim -> handler -> claim was incorrectly
    accepted (only exact-repeat was checked, not any backward regression),
    which let resume_step() return 'handler' again after a 'claim' regression
    -- silently replaying an already-completed write boundary.
    """
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "checkpoints.jsonl"
        record_checkpoint("TASK-Y", "claim", log=log)
        record_checkpoint("TASK-Y", "handler", log=log)
        try:
            record_checkpoint("TASK-Y", "claim", log=log)
            raise AssertionError("expected DurableExecutionError on backward step regression")
        except DurableExecutionError:
            pass
        # The last valid checkpoint must still be 'handler', unaffected by
        # the rejected regression attempt.
        assert resume_step("TASK-Y", log) == "submit"


def test_simulated_killed_handler_mid_task_resumes_correctly() -> None:
    """Executable chaos probe: simulate a handler that crashes right after
    'claim' (before 'handler' completes), then confirm a fresh process
    asking resume_step() picks up exactly where the crash left off.
    """
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "checkpoints.jsonl"
        record_checkpoint("TASK-CRASH", "claim", log=log, detail="claimed by agent-A")
        # Simulate crash here -- no 'handler' checkpoint recorded.

        next_step = resume_step("TASK-CRASH", log)
        assert next_step == "handler", "a fresh process must resume at 'handler', not restart at 'claim'"

        last = get_last_checkpoint("TASK-CRASH", log)
        assert last["step"] == "claim"
        assert last["detail"] == "claimed by agent-A"


def test_checkpoints_for_different_tasks_are_independent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        log = Path(tmp) / "checkpoints.jsonl"
        record_checkpoint("TASK-A", "claim", log=log)
        record_checkpoint("TASK-B", "claim", log=log)
        record_checkpoint("TASK-B", "handler", log=log)

        assert resume_step("TASK-A", log) == "handler"
        assert resume_step("TASK-B", log) == "submit"


def main() -> int:
    tests = [
        test_resume_step_starts_at_first_step_with_no_checkpoints,
        test_record_and_resume_progresses_through_steps,
        test_recording_same_step_twice_in_a_row_is_rejected,
        test_recording_an_earlier_step_after_a_later_one_is_rejected,
        test_simulated_killed_handler_mid_task_resumes_correctly,
        test_checkpoints_for_different_tasks_are_independent,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
