# Review Record: TASK-098

## Header

```text
task_id:      TASK-098
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
| 1 | Watcher main loop writes its own pid to `.locks/limit-watcher.pid` at startup; `--once` and `--dry-run` do not touch it | PASS | `main()` returns before pidfile writes for `--once`, skips pidfile writes when `args.dry_run` is true, and writes `os.getpid()` only before entering the long-running loop. A monkeypatched invocation verified long-running mode writes a numeric pidfile while `--once` and `--dry-run` leave no pidfile in a temp root. |
| 2 | Existing 15 watcher tests still pass; suite green | PASS | `python3 MAP_System/tests/test_limit_watcher.py` passed 15/15. `MAP_System/scripts/run_tests.sh` passed 23/23, including the new runner classification test from the parallel TASK-097 lane. |

## Files Reviewed

- `MAP_System/scripts/limit_watcher.py`
- `MAP_System/tasks/TASK-098.json`

## Forbidden Changes

- No change to `--once` behavior.
- No pidfile write during `--dry-run`.
- No new watcher spawn, claim, or headless behavior.
- No changes to the existing hcom resume command shape.

## Notes

The worktree also contains TASK-097 runner/state cleanup in
`MAP_System/graph/runner.py`, `MAP_System/tests/test_runner_task_classification.py`,
and related task/status files. Those changes were not included in this
TASK-098 verdict except as part of the full-suite environmental check.

The live pidfile contains `534779`, matching the submitter's reported watcher
pid. Direct `/proc/534779/cmdline` inspection was not available from this
sandbox namespace, so runtime liveness evidence is limited to the pidfile and
watcher log start lines.

## Verification

```bash
python3 -m py_compile MAP_System/scripts/limit_watcher.py
python3 MAP_System/tests/test_limit_watcher.py
MAP_System/scripts/run_tests.sh
python3 MAP_System/scripts/validate_task_graph.py
python3 MAP_System/scripts/validate_shared_state.py
python3 MAP_System/scripts/validate_events.py
python3 MAP_System/scripts/map_emergence.py validate
MAP_System/.venv/bin/python MAP_System/graph/runner.py
```

Targeted pidfile behavior check:

```text
long-running writes own pidfile
dry-run does not write pidfile
once does not write pidfile
```

Results:

```text
limit_watcher tests: 15/15 passed
full MAP suite: 23/23 passed
task graph: passed
shared state: 18 checked, 0 failures, 0 warnings
events: errors=0 warnings=33 historical warnings
emergence: 26 checked, valid
runner: submitted_tasks=[TASK-097, TASK-098], ready_tasks=[], blocked_tasks=[TASK-096]
live pidfile: 534779
```
