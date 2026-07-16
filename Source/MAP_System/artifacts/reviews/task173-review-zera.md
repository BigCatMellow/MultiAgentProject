# Review: TASK-173 Implement MAP-Only Session Replay Builder

```
task_id:      TASK-173
reviewer:     claude-lab-zera
review_date:  2026-07-14
task_owner:   codex-lab-mozu
```

Reviewer (claude-lab-zera) != task owner (codex-lab-mozu). Independence
check passes.

## Verdict

```
APPROVED
```

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | CLI can build a disposable local SQLite replay index from MAP events, task JSON, and map.db without writing canonical task/event/workflow sources | PASS | Ran `session_replay.py build` for real against the live repo: indexed 927 events, 164 tasks, `drift_findings=0`. Grepped source for `INSERT/UPDATE/DELETE INTO tasks` (the canonical table) — zero matches; the script only writes its own `task_index`/`replay_events`/etc. tables inside the disposable `runtime/session_replay.sqlite` file. `git status` on canonical sources after running build/status/task/agent/trace showed no new changes attributable to this tool. |
| 2 | CLI exposes status, task, agent, and trace read queries with deterministic JSON output suitable for mission-control integration | PASS | Ran all 4 subcommands for real: `status` (source snapshots, row/kind counts, drift list), `task TASK-172` (returned real, correct event history including the actual submission summary text), `agent`/`trace` also exercised via the test suite. Output is plain sorted JSON. |
| 3 | Build/status report drift findings for malformed events, missing task references, mirror validation failure, and source high-water metadata | PASS | All 4 drift codes present in source (`malformed_event`, `missing_task_ref`, `mirror_validation_failed`) plus `source_snapshots.high_water` metadata (e.g. `lines:927`, `tasks:164`). `test_build_records_mirror_validation_failure_when_enabled` specifically exercises the mirror-failure path. |
| 4 | Focused tests and full MAP validators pass; hcom ingestion and transcript indexing remain deferred | PASS | `test_session_replay.py` 4/4. Full suite `run_tests.sh` pass=54 fail=0 total=54. `validate_task_mirrors.py` pass. Grepped source for "hcom"/"transcript" — zero hits, confirming deferral is real, not just claimed. |

## Files Reviewed

- `MAP_System/scripts/session_replay.py`
- `MAP_System/tests/test_session_replay.py`
- `MAP_System/runtime/README.md`
- `MAP_System/runtime/.gitignore`
- `MAP_System/tasks/TASK-173.json`

## Forbidden Changes Check

- PASS: no self-review; reviewer `claude-lab-zera` is not owner `codex-lab-mozu`.
- PASS: changed files match declared `output_paths`.
- PASS: `runtime/` correctly gitignores `*.sqlite*` so the disposable index
  itself won't get committed as if it were durable state.

## Verification

Commands run (against the real repo, not just fixtures):

```bash
python3 MAP_System/scripts/session_replay.py build
python3 MAP_System/scripts/session_replay.py status
python3 MAP_System/scripts/session_replay.py task TASK-172 --limit 5
python3 MAP_System/tests/test_session_replay.py
bash MAP_System/scripts/run_tests.sh
python3 MAP_System/scripts/validate_task_mirrors.py
grep -n "INSERT INTO tasks\|UPDATE tasks\|DELETE FROM tasks" MAP_System/scripts/session_replay.py
grep -n "hcom\|transcript" MAP_System/scripts/session_replay.py
```

Results: real build succeeded with 0 drift against live data; query
commands returned correct, real data; both grep checks confirmed zero
matches (no canonical writes, no premature hcom/transcript code); full
suite and mirrors clean.

## Findings

No BLOCKER or REQUIRED findings.

One minor, non-blocking observation: `build_index()`'s return dict reports
`drift_findings` as an integer count, while `index_status()`'s return dict
reports `drift_findings` as the full list of finding dicts under the same
key name. Not a functional bug (both are internally consistent and
correctly typed for their own command), but a mission-control integration
consuming both commands should not assume the same key means the same
shape across `build` and `status` output. Worth a one-line docstring note
in a follow-up, not required for this approval.

## Notes

Directly and honestly followed TASK-172's design — same table names, same
drift codes, same "derived, never a second source of truth" framing. Good
choice testing the mirror-validation-failure drift path explicitly rather
than only the happy path. This is genuinely working, exercised
infrastructure now, not another design document — a real answer to the
operator's "implement, don't just design" directive.
