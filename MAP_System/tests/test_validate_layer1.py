#!/usr/bin/env python3
"""Tests for the Layer 1 deterministic validator cascade (TASK-162)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

import tempfile  # noqa: E402

from MAP_System.scripts.validate_layer1 import (  # noqa: E402
    run_layer1,
    maybe_set_halt,
    CORE_L1_VALIDATORS,
    DEFAULT_SEVERITY_CAP,
)
from MAP_System.scripts.halt_state import load_halt_state  # noqa: E402


def test_run_layer1_against_real_clean_repo_passes() -> None:
    """Against the real repo's current (clean) state, every core L1
    validator should pass -- this is the smoke test that the aggregation
    is wired correctly, not a fixture-only test, since these are read-only
    validators safe to run against canonical state.
    """
    report = run_layer1()
    assert report["overall_pass"] is True, report["failing"]
    assert len(report["validators"]) == len(CORE_L1_VALIDATORS)
    for r in report["validators"]:
        assert r["passed"] is True, r


def test_run_layer1_reports_per_validator_breakdown() -> None:
    report = run_layer1()
    names = {r["validator"] for r in report["validators"]}
    assert names == {name for name, _ in CORE_L1_VALIDATORS}


def test_run_layer1_does_not_reimplement_logic() -> None:
    """Structural check: validate_layer1.py should only invoke existing
    validator scripts as subprocesses, never duplicate their checks.
    """
    import inspect
    import MAP_System.scripts.validate_layer1 as vl

    source = inspect.getsource(vl)
    # No direct SQLite/file mutation or independent schema logic --
    # everything flows through subprocess.run of named scripts.
    assert "subprocess.run" in source
    assert source.count("def run_validator") == 1
    assert "CREATE TABLE" not in source
    assert "ALTER TABLE" not in source


def test_review_record_validator_is_optional() -> None:
    """validate_review is only included when a --review-record path is
    given, since it requires an explicit argument the core set doesn't have.
    """
    report_without = run_layer1()
    names_without = {r["validator"] for r in report_without["validators"]}
    assert "validate_review" not in names_without

    report_with = run_layer1(review_record=str(ROOT / "artifacts" / "reviews" / "task147-review-zera.md"), task_id="TASK-147")
    names_with = {r["validator"] for r in report_with["validators"]}
    assert "validate_review" in names_with


def test_default_severity_cap_never_writes_halt_store() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt-state.json"
        fake_failing_report = {"overall_pass": False, "failing": ["validate_task_graph"]}
        halt_id = maybe_set_halt(fake_failing_report, severity=DEFAULT_SEVERITY_CAP, halt_path=str(halt_path))
        assert halt_id is None
        assert not halt_path.exists()


def test_blocking_severity_writes_task_scoped_repair_only_halt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt-state.json"
        fake_failing_report = {"overall_pass": False, "failing": ["validate_task_graph"]}
        halt_id = maybe_set_halt(
            fake_failing_report, severity="BLOCKING", scope="task", target="TASK-999",
            set_by="validator-layer1", halt_path=str(halt_path),
        )
        assert halt_id is not None
        record = load_halt_state(str(halt_path))
        assert record["state"] == "repair_only"
        assert record["scope"] == "task"
        assert record["reason"] == "validator_blocking_anomaly"


def test_passing_report_never_sets_halt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        halt_path = Path(tmp) / "halt-state.json"
        passing_report = {"overall_pass": True, "failing": []}
        halt_id = maybe_set_halt(passing_report, severity="STRUCTURAL", halt_path=str(halt_path))
        assert halt_id is None
        assert not halt_path.exists()


def test_no_second_halt_table_is_created() -> None:
    import inspect
    import MAP_System.scripts.validate_layer1 as vl

    source = inspect.getsource(vl)
    assert "from MAP_System.scripts.halt_state import set_halt" in source
    assert "validator_halts" not in source


def main() -> int:
    tests = [
        test_run_layer1_against_real_clean_repo_passes,
        test_run_layer1_reports_per_validator_breakdown,
        test_run_layer1_does_not_reimplement_logic,
        test_review_record_validator_is_optional,
        test_default_severity_cap_never_writes_halt_store,
        test_blocking_severity_writes_task_scoped_repair_only_halt,
        test_passing_report_never_sets_halt,
        test_no_second_halt_table_is_created,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
