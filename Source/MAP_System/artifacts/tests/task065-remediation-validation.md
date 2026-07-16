# TASK-065 Remediation Validation

Owner: codex-lab-limo
Date: 2026-07-02

## Implemented

- `map_task.py create --task-id auto` reserves the next task ID under a SQLite
  write lock.
- `map_emergence.py stale` reports active stale/placeholder emergence lifecycle
  issues.
- `validate_events.py` reports legacy event schema/type aliases and can run
  strict.
- `git_operation_lock.py` provides a non-destructive repo-global operation lock.
- `reconcile_agents.py` compares durable agent state with hcom JSON input.
- `intake_request.py` gives a small operator-request worker-fit recommendation.
- `shared/canonical-repo.md` records `/home/home/Downloads/MultiAgentProject`
  as canonical, aligned with DEC-012.
- `shared/approval-calibration.md` records when to ask, continue, peer-review,
  or stop for ownership.
- `shared/current-state.md` and `shared/improvement-backlog.md` updated with
  first-pass remediation status.

## Tests

Focused tests passed:

- `test_map_task_auto_id.py`
- `test_map_emergence_stale.py`
- `test_validate_events.py`
- `test_git_operation_lock.py`
- `test_reconcile_agents.py`

Full suite:

- `MAP_System/scripts/run_tests.sh`
- Result: `pass=18 fail=0 total=18`

Validators:

- `validate_task_graph.py`: passes.
- `validate_shared_state.py`: 18 files checked, 0 failures, 0 warnings.
- `validate_decisions.py`: 12 decisions checked, 0 failures.
- `map_emergence.py validate`: 18 artifacts checked, passes.
- `validate_events.py`: 0 errors; warnings remain for historical legacy event
  shapes, as expected.

Emergence stale report:

- `map_emergence.py stale`: no findings.

## Coordination Note

`validate_task_graph.py` temporarily found a live output collision between
Claude's TASK-075 and TASK-078 (`MAP_System/emergence/`). codex-lab-limo
reported this to claude-lab-rose. claude-lab-rose narrowed the task output
paths in file mirrors; codex-lab-limo then corrected the matching SQLite
`task_output_paths` rows so future exports preserve the narrowed ownership.
Final graph validation is clean.
