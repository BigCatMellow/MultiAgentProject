# TASK-035 Promote Task Test

Task: `TASK-035`
Date: 2026-06-29
Owner: `codex-live`

## Implemented

- Added `MAP_System/scripts/promote_task.py`.
- Added HPOM READY gate validation for:
  - `objective`
  - `required_context`
  - `files_in_scope`
  - `forbidden_changes`
  - `acceptance_criteria`
  - `expected_artifacts`
  - `reviewer_role`
  - `risk`
- The script reads both SQLite task state and exported task JSON.
- SQLite currently owns the native fields it can represent:
  - `objective` via task `description`
  - `files_in_scope` via `task_output_paths`
  - `acceptance_criteria` via `task_acceptance_criteria`
- Task JSON owns the full HPOM contract until the SQLite schema grows explicit
  HPOM metadata columns.
- Added `--audit` mode for existing `READY` tasks.
- Added claim-time soft defense in `db/claims.py`: a task with no acceptance
  criteria cannot be claimed.
- Updated `map_task.py create` so incomplete tasks default to `NEEDS_SHAPING`
  instead of `READY`.
- Added `MAP_System/tests/test_promote_task.py`.
- Wired the promotion tests into `MAP_System/scripts/run_tests.sh`.

## Verification

Commands run:

```bash
python3 MAP_System/tests/test_promote_task.py
python3 -m py_compile MAP_System/scripts/promote_task.py MAP_System/db/claims.py MAP_System/scripts/map_task.py MAP_System/tests/test_promote_task.py
MAP_System/scripts/run_tests.sh
python3 MAP_System/scripts/promote_task.py --audit --db MAP_System/map.db
```

Results:

- Targeted promotion tests passed:
  - valid task promotes;
  - invalid task remains blocked;
  - CLI error names missing fields.
- Full MAP test runner passed: `pass=5 fail=0 total=5`.
- Audit mode correctly flagged `TASK-036` as missing HPOM fields. This is
  expected because `TASK-036` is still a pre-promotion READY task and should be
  shaped/promoted under the new HPOM gate before execution.

## Notes

`pytest` is not installed in this environment, so
`MAP_System/tests/test_promote_task.py` is a deterministic Python test module
that can run directly with `python3`.

## Improvements Checked

Implemented: first HPOM enforcement piece, including hard promotion gate,
claim-time soft gate, and tests.

Recommended: before starting `TASK-036`, add HPOM fields to its task JSON and
promote it through `scripts/promote_task.py`.

Not changed: SQLite schema was not expanded with HPOM-specific columns; the
script validates SQLite-native fields plus full JSON contract.
