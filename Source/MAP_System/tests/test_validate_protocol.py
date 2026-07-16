#!/usr/bin/env python3
"""Tests for the protocol/MATOCP validator and halt-store integration (TASK-162)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.validate_protocol import (  # noqa: E402
    check_matocp_token,
    check_request_format,
    check_intent_presence,
    evaluate_protocol,
    maybe_set_halt,
    DEFAULT_SEVERITY_CAP,
)
from MAP_System.scripts.halt_state import load_halt_state  # noqa: E402


def test_plain_prose_is_not_applicable() -> None:
    result = check_matocp_token("Everything looks fine, moving on to the next task.")
    assert result["applicable"] is False
    assert result["violation"] is False


def test_well_formed_ack_passes() -> None:
    result = check_matocp_token("!ACK task-149")
    assert result["applicable"] is True
    assert result["violation"] is False


def test_unrecognized_token_is_a_violation() -> None:
    result = check_matocp_token("!HALT TASK-1 reason=\"test\"")
    assert result["violation"] is True
    assert "!HALT" in result["reason"]


def test_err_without_reason_is_malformed() -> None:
    result = check_matocp_token("!ERR E001")
    assert result["applicable"] is True
    assert result["violation"] is True


def test_note_over_200_chars_is_malformed() -> None:
    long_text = "!NOTE " + ("x" * 250)
    result = check_matocp_token(long_text)
    assert result["violation"] is True


def test_request_format_requires_four_parts() -> None:
    incomplete = "Issue: something broke.\nNeeded: your call."
    result = check_request_format(incomplete, is_operator_decision_request=True)
    assert result["violation"] is True
    assert "Options" in result["reason"]

    complete = "Issue: x\nOptions: a, b\nRecommendation: a\nNeeded: approval"
    result = check_request_format(complete, is_operator_decision_request=True)
    assert result["violation"] is False


def test_missing_required_intent_is_a_violation() -> None:
    """The Protocol halt test probe's exact scenario: a broadcast message
    missing its required --intent.
    """
    result = check_intent_presence(None, required=True)
    assert result["violation"] is True
    assert "missing" in result["reason"]


def test_invalid_intent_is_a_violation() -> None:
    result = check_intent_presence("urgent", required=True)
    assert result["violation"] is True
    assert "urgent" in result["reason"]

    result = check_intent_presence("urgent", required=False)
    assert result["violation"] is True


def test_valid_intents_pass_when_required() -> None:
    for intent in ("request", "inform", "ack"):
        result = check_intent_presence(intent, required=True)
        assert result["violation"] is False, intent


def test_intent_not_required_and_absent_is_not_applicable() -> None:
    result = check_intent_presence(None, required=False)
    assert result["violation"] is False
    assert result["applicable"] is False


def test_evaluate_protocol_fails_on_missing_required_intent_broadcast() -> None:
    """End-to-end version of the Protocol halt test probe: a broadcast-style
    message with no intent, flagged as intent_required=True, must fail.
    """
    finding = evaluate_protocol(
        "Reviewed the docs, here's what I found.",
        intent=None,
        intent_required=True,
    )
    assert finding["passed"] is False
    assert any("missing" in r for r in finding["reasons"])


def test_evaluate_protocol_passes_with_valid_intent() -> None:
    finding = evaluate_protocol(
        "!ACK task-1",
        intent="ack",
        intent_required=True,
    )
    assert finding["passed"] is True


def test_evaluate_protocol_default_adjudication_is_pending_not_asserted() -> None:
    finding = evaluate_protocol("!HALT bad-token")
    assert finding["passed"] is False
    assert finding["adjudication"] == "pending", (
        "a validator finding must not assert true_positive on its own -- "
        "adjudication is a reviewer's call, per map-protocol-validator-spec.md"
    )


def test_default_severity_cap_never_writes_halt_store() -> None:
    """The core acceptance criterion: at default config, a real protocol
    defect surfaces as telemetry, never a blocking halt-store write.
    """
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt-state.json"
        finding = evaluate_protocol("!HALT bad-token")
        assert finding["passed"] is False

        halt_id = maybe_set_halt(finding, severity=DEFAULT_SEVERITY_CAP, halt_path=str(halt_path))
        assert halt_id is None
        assert not halt_path.exists(), "DRIFT severity must never write to the halt store"


def test_blocking_severity_writes_task_scoped_repair_only_halt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt-state.json"
        finding = evaluate_protocol("!HALT bad-token")

        halt_id = maybe_set_halt(
            finding, severity="BLOCKING", scope="task", target="TASK-999",
            set_by="validator-protocol", halt_path=str(halt_path),
        )
        assert halt_id is not None
        record = load_halt_state(str(halt_path))
        assert record["state"] == "repair_only"
        assert record["scope"] == "task"
        assert record["target"] == "TASK-999"
        assert record["reason"] == "validator_blocking_anomaly"


def test_structural_severity_writes_global_halt_all_dispatch() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt-state.json"
        finding = evaluate_protocol("!HALT bad-token")

        halt_id = maybe_set_halt(
            finding, severity="STRUCTURAL", set_by="validator-protocol", halt_path=str(halt_path),
        )
        assert halt_id is not None
        record = load_halt_state(str(halt_path))
        assert record["state"] == "halt_all_dispatch"
        assert record["scope"] == "global"


def test_passed_finding_never_sets_halt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt-state.json"
        finding = evaluate_protocol("!ACK task-1")
        assert finding["passed"] is True

        halt_id = maybe_set_halt(finding, severity="STRUCTURAL", halt_path=str(halt_path))
        assert halt_id is None
        assert not halt_path.exists()


def test_no_second_halt_table_is_created() -> None:
    """Structural check: this module must write into TASK-159's halt
    store API, never define its own table/store.
    """
    import inspect
    import MAP_System.scripts.validate_protocol as vp

    source = inspect.getsource(vp)
    assert "from MAP_System.scripts.halt_state import set_halt" in source
    assert "CREATE TABLE" not in source
    assert "validator_halts" not in source


def main() -> int:
    tests = [
        test_plain_prose_is_not_applicable,
        test_well_formed_ack_passes,
        test_unrecognized_token_is_a_violation,
        test_err_without_reason_is_malformed,
        test_note_over_200_chars_is_malformed,
        test_request_format_requires_four_parts,
        test_missing_required_intent_is_a_violation,
        test_invalid_intent_is_a_violation,
        test_valid_intents_pass_when_required,
        test_intent_not_required_and_absent_is_not_applicable,
        test_evaluate_protocol_fails_on_missing_required_intent_broadcast,
        test_evaluate_protocol_passes_with_valid_intent,
        test_evaluate_protocol_default_adjudication_is_pending_not_asserted,
        test_default_severity_cap_never_writes_halt_store,
        test_blocking_severity_writes_task_scoped_repair_only_halt,
        test_structural_severity_writes_global_halt_all_dispatch,
        test_passed_finding_never_sets_halt,
        test_no_second_halt_table_is_created,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
