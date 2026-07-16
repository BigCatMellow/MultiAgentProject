# Review Record: TASK-119

## Header

```text
task_id:      TASK-119
reviewer:     codex-lab-lema
review_date:  2026-07-03
task_owner:   codex-lab-dino
```

Reviewer != owner. Independence check passes.

## Verdict

```text
APPROVED
```

## Acceptance Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | RnS detects expired `IN_PROGRESS` claims as a queue-stall condition even when no `READY` work exists | PASS | `stale_claims()` queries expired `IN_PROGRESS` leases directly from SQLite, independent of `READY` work. `poll_once()` evaluates stale claims outside the work-dispatch loop result. |
| 2 | RnS sends a throttled request to the stale claim owner/claimer with resume/submit/release/pause options instead of silently idling | PASS | `decide_stale_claim_owner_nudges()` groups by `claimed_by`/`owner` and throttles per task for 30 minutes; the hcom request names resume, submit, release/rework, or intentional pause options. |
| 3 | Focused `limit_watcher` tests, `validate_task_graph.py`, `validate_events.py`, and full `run_tests.sh` pass | PASS | Verification commands below passed. |

## Files Reviewed

- `MAP_System/scripts/limit_watcher.py`
- `MAP_System/tests/test_limit_watcher.py`
- `MAP_System/artifacts/tests/task-119-rns-stale-claim-owner-nudge.md`
- `MAP_System/tasks/TASK-119.json`
- `MAP_System/workflow/task_graph.json`

## Findings

No blocker or required findings.

## Forbidden Changes Check

- PASS: Existing visible resume behavior still uses `hcom r <agent> --terminal wezterm-tab --go`; no headless helper path was added.
- PASS: The new stale-claim path sends message-only hcom requests and does not auto-claim, auto-release, or reassign another agent's task.
- PASS: RnS recorded-reset, presumed-down, check-in, and work-dispatch throttles remain in place.
- PASS: TASK-119 output paths are limited to the RnS script, focused test, and test artifact.

## Security Second Pass

Scope: TASK-119 adds a new hcom write path from `limit_watcher.py`.

| Check | Result | Evidence |
|---|---|---|
| Shell injection | PASS | hcom is invoked with a subprocess argument list, not shell interpolation. The message body is passed after `--`. |
| Target injection | PASS | Recipient is constructed as one argv item (`@{name}`); malformed task data cannot create extra command flags. Empty task IDs or agent names are skipped. |
| Database access | PASS | `stale_claims()` opens SQLite in read-only URI mode and performs a fixed query. |
| Authority boundary | PASS | The watcher asks the stale claim owner to act; it does not mutate task ownership or status. |
| Throttle/flooding | PASS | Nudges are throttled per task by `STALE_CLAIM_OWNER_NUDGE_SECONDS = 1800`. |

## Verification

```bash
MAP_System/.venv/bin/python MAP_System/tests/test_limit_watcher.py
MAP_System/.venv/bin/python -m py_compile MAP_System/scripts/limit_watcher.py MAP_System/tests/test_limit_watcher.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_shared_state.py
MAP_System/scripts/run_tests.sh
```

Results:

```text
focused limit_watcher: PASS, 16 tests
py_compile: PASS
task graph: PASS
events: errors=0 warnings=33 historical warnings
shared state: 18 checked, 0 failures, 0 warnings
full MAP suite: pass=33 fail=0 total=33
```
