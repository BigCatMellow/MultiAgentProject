# TASK-119 RnS Stale-Claim Owner Nudge

task_id: TASK-119
owner: codex-lab-dino
date: 2026-07-03

## Scope

Hardened Rise & Shine so a recovered agent does not silently idle when the
queue is stalled by another agent's expired `IN_PROGRESS` claim.

## Files

- `MAP_System/scripts/limit_watcher.py`
- `MAP_System/tests/test_limit_watcher.py`

## Change

- Added `stale_claims()` to read expired `IN_PROGRESS` claims from SQLite.
- Added `decide_stale_claim_owner_nudges()` to group stale claims by claimer
  and throttle reminders per task.
- Added a request-format hcom nudge to the stale claim owner with explicit
  options: resume and submit, release/rework, or state an intentional pause.
- Added a focused regression test for the TASK-117 failure mode.

## Commands

- `MAP_System/.venv/bin/python MAP_System/tests/test_limit_watcher.py`
  - PASS: 16 limit watcher tests, including stale-claim owner nudge regression
- `MAP_System/.venv/bin/python -m py_compile MAP_System/scripts/limit_watcher.py MAP_System/tests/test_limit_watcher.py`
  - PASS
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py`
  - PASS
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py`
  - PASS: 0 errors, 33 known legacy warnings
- `MAP_System/scripts/run_tests.sh`
  - PASS: 33 passed, 0 failed
