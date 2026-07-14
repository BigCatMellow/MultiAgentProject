# TASK-159 Review - melo

task_id: TASK-159
reviewer: task153review-melo
task_owner: codex-lab-mozu
review_date: 2026-07-14

## Verdict

CHANGES_REQUESTED

## No-Self-Review Check

- TASK-159 owner/submitter is `codex-lab-mozu`.
- Review performed by independent bounded reviewer `task153review-melo`.
- I did not edit TASK-159 implementation files and did not approve the task in DB.

## Acceptance Criteria Check

| # | Result | Evidence |
|---|---|---|
| 1 | PARTIAL | `MAP_System/scripts/halt_state.py` implements a durable human-inspectable JSON halt store with the TASK-151 fields, scoped states, clear evidence fields, and set/clear authority checks. However, one clear-authority path violates the global-halt rule; see REQUIRED finding R1. |
| 2 | PASS | `MAP_System/scripts/cost_governance.py` implements cost counters, validates token/cost fields, records per-scope budget counters, and treats unknown paid dispatch cost as a halt condition rather than zero cost. |
| 3 | PASS | `MAP_System/graph/runner.py`, `MAP_System/db/claims.py`, and `MAP_System/scripts/agent_loop.py` read the shared halt state path before routing or claiming and suppress blocked paid/global dispatch while leaving permitted review/repair/operator/read-only/local lanes available according to halt state. |
| 4 | PARTIAL | Tests cover paid-dispatch halt, global halt for `operator_stop`, cost missing/unknown handling, runner paid-task suppression, and agent-loop claim blocking. They do not cover the validator-triggered global halt clear-authority case in R1. |

## Files Reviewed

- `AGENTS.md`
- `docs/agent-quickstart.md`
- `docs/project-map.md`
- `MAP_System/AGENTS.md`
- `MAP_System/tasks/TASK-159.json`
- `MAP_System/tasks/TASK-151.json`
- `MAP_System/artifacts/planning/map-cost-governance-spec.md`
- `MAP_System/artifacts/planning/map-kill-switch-spec.md`
- `MAP_System/artifacts/planning/map-validator-halt-state-spec.md`
- `MAP_System/scripts/halt_state.py`
- `MAP_System/scripts/cost_governance.py`
- `MAP_System/db/claims.py`
- `MAP_System/graph/runner.py`
- `MAP_System/scripts/agent_loop.py`
- `MAP_System/tests/test_halt_state.py`
- `MAP_System/tests/test_cost_governance.py`
- `MAP_System/tests/test_runner_task_classification.py`
- `MAP_System/scripts/run_tests.sh`
- `MAP_System/scripts/validate_review.py`

## Forbidden Changes Check

- PASS: reviewer is independent from task owner.
- PASS: this review only adds `MAP_System/artifacts/reviews/task159-review-melo.md`.
- PASS: I did not edit TASK-159 implementation/test files and did not approve the task in DB.
- PASS: security second-pass gate is not required as a separate review because TASK-159 does not add a network-facing component. The authority-control issue found below is handled as a blocking functional/security finding in this review.

## Findings

### R1 - REQUIRED - Validator-triggered global halts can be cleared by a validator identity

`MAP_System/scripts/halt_state.py:117`-`130` allows any identity whose normalized name starts with `validator` to clear a halt when `reason == "validator_blocking_anomaly"`, regardless of whether the halt is global. This bypasses the TASK-151 kill-switch rule that global halts may be cleared by command-center only, and it conflicts with the TASK-152 validator-halt rule that structural/global validator halts escalate to command-center.

Evidence:

- `map-kill-switch-spec.md` says `Clear global halt | command-center only`.
- `map-validator-halt-state-spec.md` says `STRUCTURAL` validator halts are `scope=global` and `STRUCTURAL` clears are command-center only.
- Manual probe:

```text
set_halt(state='halt_all_dispatch', reason='validator_blocking_anomaly', set_by='validator', scope='global', ...)
clear_halt(cleared_by='validator', clear_reason='validator self-clear', ...)
=> cleared_by validator state clear
```

This means the validator producer of a global halt can also clear it without command-center approval. Fix by making global halt clear authority command-center-only before the validator-reason branch, and add a regression test for a `halt_all_dispatch` / `scope=global` / `reason=validator_blocking_anomaly` record.

## Validators

- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_halt_state.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_cost_governance.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_runner_task_classification.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/scripts/integration_test.py`
  - Result: 11/11 passed.
- PASS: `MAP_System/scripts/run_tests.sh`
  - Result: `SUMMARY pass=41 fail=0 total=41`.
- MANUAL PROBE: validator identity can currently clear a validator-triggered global halt; this confirms finding R1.
