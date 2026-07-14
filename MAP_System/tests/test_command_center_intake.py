#!/usr/bin/env python3
"""Tests for the command-center intake wrapper (TASK-167)."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.command_center_intake import (  # noqa: E402
    run_intake,
    append_intake_event,
    validate_wrapper_output,
    IntakeWrapperError,
)
from MAP_System.scripts.intake_request import dispatch_packet  # noqa: E402


def test_run_intake_produces_packet_event_and_route() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        event_log = Path(tmp) / "events.jsonl"
        result = run_intake("Review the event log", owner="test-owner", event_log=event_log)

        assert result["packet"]["owner"] == "test-owner"
        assert result["packet"]["classification"]["task_type"] == "audit"
        assert result["next_route"] is not None
        assert event_log.exists()

        event = json.loads(event_log.read_text(encoding="utf-8").splitlines()[0])
        assert event["type"] == "PROGRESS"
        assert event["action"] == "intake"
        assert "task_type=audit" in event["summary"]


def test_no_event_flag_skips_event_write() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        event_log = Path(tmp) / "events.jsonl"
        result = run_intake("Fix the bug", owner="test-owner", event_log=event_log, record_event=False)
        assert result["event"] is None
        assert not event_log.exists()


def test_wrapper_output_passes_protocol_validation_for_normal_intake() -> None:
    """The wrapper composes intake_request.py's own hcom_inform format,
    which must itself pass the protocol validator -- not be exempt from
    the checks the whole system exists to route work through.
    """
    packet = dispatch_packet("Push and publish the release")
    classification = packet["classification"]
    hcom_inform = (
        f"Intake: worker_fit={classification['worker_fit']} risk={classification['risk']} "
        f"needs_task={classification['needs_task']} task_tier={classification['task_tier']} "
        f"gap_score={classification['gap_score']} reviewer={classification['reviewer']} "
        f"note={classification['note']}"
    )
    finding = validate_wrapper_output(hcom_inform)
    assert finding["passed"] is True


def test_wrapper_output_validation_raises_on_malformed_text() -> None:
    """Direct unit test of the validation guard itself: a MATOCP-token-
    shaped string using an unrecognized token must be rejected, proving
    the wrapper's validation call is not a no-op.
    """
    try:
        validate_wrapper_output("!UNKNOWN_TOKEN this should fail")
        raise AssertionError("expected IntakeWrapperError")
    except IntakeWrapperError:
        pass


def test_append_intake_event_records_key_classification_fields() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        event_log = Path(tmp) / "events.jsonl"
        packet = dispatch_packet("Build the new validator halt gate", owner="codex-test")
        event = append_intake_event(packet, task_id="TASK-167", event_log=event_log)

        assert event["task_id"] == "TASK-167"
        assert event["sender"] == "command-center-intake"
        assert "task_type=implementation" in event["summary"]
        assert "owner=codex-test" in event["summary"]

        logged = json.loads(event_log.read_text(encoding="utf-8").splitlines()[0])
        assert logged == event


def test_does_not_reimplement_intake_classification() -> None:
    """Structural check: the wrapper must call dispatch_packet(), not
    duplicate its regex/classification rules.
    """
    import inspect
    import MAP_System.scripts.command_center_intake as cci

    source = inspect.getsource(cci)
    assert "from MAP_System.scripts.intake_request import dispatch_packet" in source
    assert "re.search" not in source, "wrapper must not reimplement intake_request.py's classification regexes"


def main() -> int:
    tests = [
        test_run_intake_produces_packet_event_and_route,
        test_no_event_flag_skips_event_write,
        test_wrapper_output_passes_protocol_validation_for_normal_intake,
        test_wrapper_output_validation_raises_on_malformed_text,
        test_append_intake_event_records_key_classification_fields,
        test_does_not_reimplement_intake_classification,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
