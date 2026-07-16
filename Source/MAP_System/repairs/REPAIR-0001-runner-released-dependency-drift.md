# Repair Record

Repair ID: REPAIR-0001
Related task: TASK-113
Found by: codex-lab-dino
Date: 2026-07-03
Severity: DRIFT
Status: APPLIED

## What was found

`MAP_System/graph/runner.py` classifies dependency satisfaction using only
`DONE` and `APPROVED` task statuses, while
`MAP_System/scripts/validate_task_graph.py` treats `RELEASED` as a terminal
status. As a result, TASK-113 is listed under `blocked_tasks` even though its
dependencies TASK-109 and TASK-111 are both `RELEASED`.

## Surfaced by

Manual route check with `MAP_System/.venv/bin/python MAP_System/graph/runner.py`
after TASK-109 and TASK-111 were released, followed by source inspection of
`MAP_System/graph/runner.py` and `MAP_System/scripts/validate_task_graph.py`.

## Severity rationale

DRIFT: canonical task/dependency state and validator semantics disagree with
the live route classification. The issue misroutes dependency-satisfied work,
but it is reversible and does not corrupt task state.

## Proposed or applied fix

Applied in TASK-116:

- `graph/runner.py` now treats `DONE`, `APPROVED`, and `RELEASED` as
  dependency-satisfying statuses. `RETIRED` remains
  non-dependency-satisfying per TASK-100: retired duplicate/cancelled tasks are
  terminal for validation cleanup, but do not provide completed output to
  downstream dependencies.
- `tests/test_runner_task_classification.py` now includes a regression test
  proving a READY task with a RELEASED dependency is routed to `ready_tasks`.
  It also includes a negative regression proving a READY task with only a
  RETIRED dependency remains blocked.

## Authority check

- [x] DRIFT or mechanical BLOCKING — core agent applied directly
- [ ] Judgment-requiring BLOCKING — proposed via hcom before applying
- [ ] STRUCTURAL — proposed to command-center, not yet applied without approval

## Verification

TASK-116 verification:

- `MAP_System/.venv/bin/python MAP_System/tests/test_runner_task_classification.py` - PASS
- RETIRED dependency repro from review - PASS; dependent READY task remains blocked
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py` - PASS
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_repair_artifacts.py` - PASS
- `MAP_System/.venv/bin/python MAP_System/graph/runner.py` - PASS; no false `blocked_tasks` for released dependencies
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py` - PASS; 0 errors, 33 known legacy warnings
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_shared_state.py --shared-dir MAP_System/shared` - PASS; 18 files checked, 0 failures, 0 warnings
- `MAP_System/scripts/run_tests.sh` - PASS; 33 passed, 0 failed

## Recurrence check

- [x] First occurrence of this drift class
- [ ] Repeat — logged in `shared/improvement-backlog.md`: NONE yet
- [x] Repeat — permanent fix proposed (validator/template/decision): TASK-116 released/retired dependency regression tests

## Notes

TASK-116 intentionally preserves TASK-100 semantics: `RETIRED` is terminal for
stale-card cleanup, but does not satisfy dependency expectations.
