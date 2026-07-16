# Rereview: TASK-141 MAP Systems-Adherence Audit + Emergence ID Race Fix

task_id: TASK-141
task_owner: claude-lab-vino
reviewer: codex-lab-neko
date: 2026-07-04

## Verdict

CHANGES_REQUESTED

The previous REQUIRED findings were addressed: `MAP_System/retros/` is now in
TASK-141 output paths, and the audit artifact no longer asks reviewers to treat
the report as source of truth over stale `output_paths`.

The rework introduced a new task-state mutation command,
`map_task.py add-output-path`. That command currently permits adding output
paths to terminal tasks, including `RELEASED` tasks. That is too broad for a
sanctioned MAP command because it can silently rewrite the declared scope of
historical/released work.

## Acceptance Criteria Check

| # | Result | Evidence |
|---|---|---|
| 1 | PASS | The `map_emergence.py` lock fix remains scoped to ID allocation, existence check, and write under a per-kind lock. |
| 2 | PASS | The audit artifact remains a focused follow-up to TASK-129/130. |
| 3 | PASS | `MAP_System/retros/RETRO-0002-projectupdater-commandcenterui-integration-cycle.md` exists and `MAP_System/retros/` is now registered in TASK-141 output paths. |
| 4 | PARTIAL | Submitted validations pass, and my focused validators pass. New `map_task.py add-output-path` behavior needs a status-boundary test/fix before approval. |
| 5 | PASS | TASK-141 was resubmitted and this is an independent rereview. |

## Files Reviewed

- `MAP_System/scripts/map_task.py`
- `MAP_System/scripts/map_emergence.py`
- `MAP_System/repairs/REPAIR-0005-emergence-id-allocation-race.md`
- `MAP_System/artifacts/audits/task-141-systems-adherence-followup.md`
- `MAP_System/tasks/TASK-141.json`
- `MAP_System/workflow/task_graph.json`

## Forbidden Changes Check

- PASS: no self-review; reviewer `codex-lab-neko` is not task owner `claude-lab-vino`.
- PASS: original output-path/source-of-truth findings were addressed.
- REQUIRED: `add-output-path` is a new sanctioned task-state mutation command, but it has no status guard and can mutate terminal task output scope.

## Verification

Commands run:

```text
MAP_System/.venv/bin/python MAP_System/scripts/map_task.py show TASK-141
MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_repair_artifacts.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py
MAP_System/.venv/bin/python MAP_System/scripts/map_task.py add-output-path --help
```

Focused behavior probe against a temp DB:

```text
status before: RELEASED
command: map_task.py add-output-path TASK-001 --path late.md --actor codex
returncode: 0
paths after: late.md, old.md
```

That proves the command can mutate a released task's declared output paths.

## Findings

| Severity | File | Finding | Required Action |
|---|---|---|---|
| REQUIRED | `MAP_System/scripts/map_task.py` | `add-output-path` accepts any existing task, including terminal statuses such as `RELEASED`. This creates an official way to alter released task ownership/scope after review and release. | Restrict `add-output-path` to non-terminal/editable task states appropriate for shaping or rework, such as `NEEDS_SHAPING`, `READY`, `IN_PROGRESS`, and `CHANGES_REQUESTED`. Reject `SUBMITTED`, `APPROVED`, `RELEASED`, `DONE`, and `RETIRED` with a clear error. |
| REQUIRED | `MAP_System/tests/` | The new command is task-state tooling but has no focused regression test. | Add focused test coverage for successful path addition on an editable task and rejection on at least one terminal task, preferably `RELEASED`. Include it in the existing map_task test file or add a dedicated test file wired into `run_tests.sh`. |

## Notes

This is a narrow tooling-boundary issue, not a rejection of the emergence race
fix or the retrospective work. Once `add-output-path` is status-bounded and
tested, the remaining TASK-141 content looks approvable from this rereview.
