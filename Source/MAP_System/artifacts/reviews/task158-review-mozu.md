task_id: TASK-158
reviewer: codex-lab-mozu
task_owner: command-center
review_date: 2026-07-14

## Verdict

CHANGES_REQUESTED

## Findings

1. REQUIRED: Non-dry reclaim mutates SQLite without exporting mirrors or validating mirror consistency.

   Evidence: `MAP_System/scripts/liveness_reaper.py` `reclaim_stale_claims(..., dry_run=False)` calls `expire_leases(db_path=db_path)` and appends events, but it does not run `MAP_System/migration/export_to_files.py` or `MAP_System/scripts/validate_task_mirrors.py` afterward. TASK-158 acceptance criterion 2 requires reaper actions to go through sanctioned DB helpers and be followed by `validate_task_mirrors.py` passing. The TASK-150 spec also says reclaim should return the task through SQLite helpers, then export, then validate. As written, a real reclaim can leave SQLite and file mirrors divergent until some unrelated later export occurs.

2. REQUIRED: Dead-letter records are not replayable back to READY and do not include a documented replay command.

   Evidence: `dead_letter_task()` appends a minimal JSONL record with `dead_letter_id`, `task_id`, `agent_id`, `detected_at`, `reason`, `replay_status`, and `source`, but no `replay_command`, no replay function, and no supported transition that returns the task to `READY`. The focused test only verifies that a record is appended. TASK-158 acceptance criterion 4 requires dead-letter records to be replayable back to READY without hand-editing `task_graph.json`, per a documented replay command and focused test.

## Acceptance Criteria Check

| # | Result | Evidence |
|---|---|---|
| 1 | PASS | `test_all_states_in_vocabulary` and classification tests cover `alive`, `working`, `blocked`, `idle`, `suspect`, `broken`, and `standby`. |
| 2 | FAIL | Reclaim uses `expire_leases()`, but real reclaim is not followed by export or `validate_task_mirrors.py` from the implementation path. |
| 3 | PARTIAL | `reclaim_stale_claims`, `dead_letter_task`, and `circuit_breaker_signal` append canonical-looking `PROGRESS` events. The review did not find a problem with the event shape. |
| 4 | FAIL | Dead-letter append exists, but replay is not implemented or documented with a replay command. |
| 5 | PASS | `circuit_breaker_signal()` is accounting-only and does not block dispatch. |

## Verification Run

- PASS: `MAP_System/scripts/run_tests.sh` reported `SUMMARY pass=41 fail=0 total=41`.
- PASS: `MAP_System/.venv/bin/python MAP_System/scripts/map_task.py show TASK-158` shows `SUBMITTED`.
- PASS: `MAP_System/.venv/bin/python MAP_System/scripts/validate_task_mirrors.py`.

## Required Fix Scope

- Add an acted reclaim path that exports file mirrors and validates them before returning success, or explicitly fails/rolls forward when validation fails.
- Add a replayable dead-letter path with a documented replay command and a focused test proving a dead-lettered task can be restored through a supported transition without hand-editing generated task files.
