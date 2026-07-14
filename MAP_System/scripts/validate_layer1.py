#!/usr/bin/env python3
"""Layer 1 deterministic validator cascade (TASK-162, from map-semantic-validator-spec.md).

Composes MAP's existing deterministic validators into one callable check.
Adds no new validation logic of its own -- it runs each named validator as a
subprocess and aggregates pass/fail, per the spec's requirement that Layer 1
is "wire these together as one Layer 1," not a rebuild.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.halt_state import set_halt  # noqa: E402

DEFAULT_SEVERITY_CAP = "DRIFT"
ESCALATABLE_SEVERITIES = ("DRIFT", "BLOCKING", "STRUCTURAL")

CORE_L1_VALIDATORS: list[tuple[str, list[str]]] = [
    ("validate_task_mirrors", [sys.executable, str(ROOT / "scripts" / "validate_task_mirrors.py")]),
    ("validate_events", [sys.executable, str(ROOT / "scripts" / "validate_events.py"), "--fail-on-new"]),
    ("validate_task_graph", [sys.executable, str(ROOT / "scripts" / "validate_task_graph.py")]),
    ("validate_shared_state", [sys.executable, str(ROOT / "scripts" / "validate_shared_state.py")]),
    ("validate_decisions", [sys.executable, str(ROOT / "scripts" / "validate_decisions.py")]),
]


def run_validator(name: str, cmd: list[str]) -> dict:
    result = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True, check=False)
    return {
        "validator": name,
        "passed": result.returncode == 0,
        "returncode": result.returncode,
        "stdout_tail": "\n".join(result.stdout.splitlines()[-5:]),
        "stderr_tail": "\n".join(result.stderr.splitlines()[-5:]) if result.stderr else "",
    }


def run_layer1(review_record: str | None = None, task_id: str | None = None) -> dict:
    """Run every core L1 validator plus, optionally, validate_review.py for a
    specific review record (it requires an explicit path, so it is not part
    of the always-run core set).
    """
    results = [run_validator(name, cmd) for name, cmd in CORE_L1_VALIDATORS]

    if review_record:
        cmd = [sys.executable, str(ROOT / "scripts" / "validate_review.py"), "--review-record", review_record]
        if task_id:
            cmd += ["--task-id", task_id]
        results.append(run_validator("validate_review", cmd))

    overall_pass = all(r["passed"] for r in results)
    return {
        "overall_pass": overall_pass,
        "validators": results,
        "failing": [r["validator"] for r in results if not r["passed"]],
    }


def maybe_set_halt(
    report: dict,
    *,
    severity: str = DEFAULT_SEVERITY_CAP,
    scope: str = "task",
    target: str | None = None,
    set_by: str = "validator-layer1",
    halt_path: str | None = None,
) -> str | None:
    """Write into TASK-159's shared halt store on a BLOCKING/STRUCTURAL
    L1 finding -- same reconciled design as validate_protocol.py's
    maybe_set_halt, never a second halt table. A DRIFT-severity finding
    (the shipped default) never calls set_halt; it is telemetry only.
    """
    if report["overall_pass"]:
        return None
    if severity not in ESCALATABLE_SEVERITIES:
        raise ValueError(f"unknown severity: {severity}")
    if severity == "DRIFT":
        return None

    state = "halt_all_dispatch" if severity == "STRUCTURAL" else "repair_only"
    halt_scope = "global" if severity == "STRUCTURAL" else scope
    record = set_halt(
        state=state,
        reason="validator_blocking_anomaly",
        set_by=set_by,
        scope=halt_scope,
        target=target if halt_scope != "global" else None,
        path=halt_path,
    )
    return record["halt_id"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-record", help="Optional review record path to also validate")
    parser.add_argument("--task-id", help="Expected task ID for --review-record cross-check")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run_layer1(args.review_record, args.task_id)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for r in report["validators"]:
            status = "PASS" if r["passed"] else "FAIL"
            print(f"{status} {r['validator']}")
            if not r["passed"]:
                if r["stdout_tail"]:
                    print(f"  stdout: {r['stdout_tail']}")
                if r["stderr_tail"]:
                    print(f"  stderr: {r['stderr_tail']}")
        print(f"SUMMARY overall_pass={report['overall_pass']} failing={report['failing']}")

    return 0 if report["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
