# TASK-116 Runner Released Dependencies Repair

task_id: TASK-116
owner: codex-lab-dino
date: 2026-07-03

## Scope

Fixed the route-classification drift recorded in
`MAP_System/repairs/REPAIR-0001-runner-released-dependency-drift.md`.

## Files

- `MAP_System/graph/runner.py`
- `MAP_System/tests/test_runner_task_classification.py`
- `MAP_System/repairs/REPAIR-0001-runner-released-dependency-drift.md`

## Change

`graph/runner.py` now treats `DONE`, `APPROVED`, and `RELEASED` as
dependency-satisfying statuses. `RETIRED` remains non-dependency-satisfying per
TASK-100: retired duplicate/cancelled tasks are terminal for cleanup, but do
not provide completed output to downstream dependencies.

## Commands

- `MAP_System/.venv/bin/python MAP_System/tests/test_runner_task_classification.py`
  - PASS: includes released-dependency and retired-dependency regressions
- `MAP_System/.venv/bin/python -c "from MAP_System.graph.runner import evaluate_tasks; ..."`
  - PASS: RETIRED dependency check returns `done_task_ids=[]`, `ready_tasks=[]`, `blocked_tasks=['TASK-B']`
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py`
  - PASS
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_repair_artifacts.py`
  - PASS
- `MAP_System/.venv/bin/python MAP_System/graph/runner.py`
  - PASS: released dependencies now appear in `done_task_ids`; no false block for TASK-113 class
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py`
  - PASS: 0 errors, 33 known legacy warnings
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_shared_state.py --shared-dir MAP_System/shared`
  - PASS: 18 files checked, 0 failures, 0 warnings
- `MAP_System/scripts/run_tests.sh`
  - PASS: 33 passed, 0 failed
