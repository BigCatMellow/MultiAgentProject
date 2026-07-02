# Review Record: TASK-095

## Header

```text
task_id:      TASK-095
reviewer:     codex-lab-lema
review_date:  2026-07-02
task_owner:   claude-lab-zaro
```

Reviewer != owner. Independence check passes.

## Verdict

```text
APPROVED
```

## Acceptance Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Watcher nudges live listening agents when claimable READY tasks exist, listing task ids, at most once per window per agent | PASS | `actionable_work()` reads `map.db` read-only and includes READY tasks with `attempt < max_attempts`. `decide_work_nudges()` targets only live `listening` agents idle at least 120 seconds, and `state["work_nudges"]` throttles per agent for 1800 seconds. `describe_work()` emits bounded task-id listings. |
| 2 | All TASK-084 suppression cases hold (claimed, standby, out_of_tokens, non-listening, recently nudged) | PASS | The work-dispatch path reuses `classify_live()` and `CHECKIN_SAFE_STATUSES`, suppresses durable records with any `reason`, suppresses durable non-available statuses, suppresses agents in `claimed_agent_ids()`, and suppresses recently nudged agents. Unit coverage includes active, dead, fresh-idle, claimed, declared standby, inactive, and throttle cases. |
| 3 | No auto-claim/auto-spawn behavior; nudges are plain hcom messages | PASS | The new TASK-095 path only runs `hcom send @agent --intent request --name limit-watcher -- ...`. It does not call `hcom r`, `hcom term`, claim scripts, or spawn helpers. The pre-existing RnS resume path remains limited to usage-limit recovery and still uses visible `--terminal wezterm-tab`. |
| 4 | Watcher test suite passes with new cases; full suite green | PASS | `python3 MAP_System/tests/test_limit_watcher.py` passed 15/15, including `test_work_dispatch_logic()`. `MAP_System/scripts/run_tests.sh` passed 22/22. |

## Files Reviewed

- `MAP_System/scripts/limit_watcher.py`
- `MAP_System/tests/test_limit_watcher.py`
- `MAP_System/notes/limit-exhaustion-protocol.md`
- `MAP_System/scripts/start-limit-watcher.sh`
- `MAP_System/tasks/TASK-095.json`
- `MAP_System/tasks/TASK-096.json`
- `MAP_System/tasks/TASK-097.json`
- `MAP_System/workflow/task_graph.json`

## Forbidden Changes

- No automatic task claiming.
- No helper or agent spawning in the work-dispatch path.
- No headless hcom launch behavior.
- No self-review nudge when an agent's only actionable item is its own submission.
- No broadening of check-in eligibility to active, blocked, waiting, dead, declared, or claimed agents.

## Notes

The LangGraph runner reports `TASK-096` in `ready_tasks` even though SQLite and
the exported task file show `TASK-096` as `BLOCKED`. This is from existing
runner classification behavior that treats dependency-satisfied `BLOCKED`
tasks as ready unless they require an unavailable agent. The state cleanup is
already tracked by `TASK-097` and is not caused by the TASK-095 watcher change.

The live watcher pidfile was stale during review (`520835` no longer existed).
`MAP_System/scripts/start-limit-watcher.sh` removed the stale pidfile and
reported a verified restart with the 5400 second default. The sandbox could not
inspect the restarted pid after wrapper exit, matching the PID-namespace caveat
documented in the wrapper, but the log shows the new `interval=5400s` start.

## Verification

```bash
python3 MAP_System/tests/test_limit_watcher.py
MAP_System/scripts/run_tests.sh
python3 MAP_System/scripts/limit_watcher.py --once --dry-run
python3 MAP_System/scripts/validate_task_graph.py
MAP_System/.venv/bin/python MAP_System/graph/runner.py
python3 MAP_System/scripts/validate_shared_state.py
python3 MAP_System/scripts/validate_events.py
python3 MAP_System/scripts/map_emergence.py validate
MAP_System/scripts/start-limit-watcher.sh
```

Results:

```text
limit_watcher tests: 15/15 passed
full MAP suite: 22/22 passed
dry-run watcher poll: no output in current live state
task graph: passed
runner: loaded SQLite and routed submitted tasks to review
shared state: 18 checked, 0 failures, 0 warnings
events: errors=0 warnings=33 historical warnings
emergence: 26 checked, valid
watcher restart: stale pidfile removed, interval 5400s start reported
```
