# Review: TASK-177 Fix liveness_reaper.py raw hcom JSON input

```
task_id:      TASK-177
reviewer:     codex-lab-mozu
review_date:  2026-07-14
task_owner:   command-center
```

Reviewer (`codex-lab-mozu`) is not the task owner (`command-center`).
Independence check passes.

## Verdict

```
APPROVED
```

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `normalize_hcom_status()` accepts raw hcom list JSON and already agent-keyed dict input | PASS | Function handles dict passthrough and list normalization keyed by `name`/`base_name`; focused tests cover both shapes. |
| 2 | CLI no longer crashes on real `hcom list --json` shape | PASS | Re-ran `liveness_reaper.py --hcom-json` against a list-shaped fixture and it emitted JSON successfully with `codex-lab-mozu` classified from `hcom:active`. |
| 3 | Regression tests cover both input shapes and malformed input | PASS | `test_normalize_hcom_status_passes_through_agent_keyed_dict`, `test_normalize_hcom_status_converts_raw_hcom_list_shape`, `test_normalize_hcom_status_rejects_unknown_shape`, and end-to-end normalize/build snapshot test all pass. |

## Files Reviewed

- `MAP_System/scripts/liveness_reaper.py`
- `MAP_System/tests/test_liveness_reaper.py`
- `MAP_System/tasks/TASK-177.json`

## Forbidden Changes Check

- PASS: no self-review.
- PASS: output paths are limited to the liveness reaper script and its focused tests.
- PASS: no external CommandCenterUI edits.

## Verification

Commands run:

```bash
python3 MAP_System/tests/test_liveness_reaper.py
python3 MAP_System/scripts/liveness_reaper.py --hcom-json /tmp/task177-hcom-list.json --snapshot-out /tmp/task177-liveness.md --json
bash MAP_System/scripts/run_tests.sh
python3 MAP_System/scripts/validate_task_mirrors.py
python3 MAP_System/scripts/validate_task_graph.py
python3 MAP_System/scripts/validate_events.py --fail-on-new
```

Results:

- Focused liveness tests passed.
- Raw list-shaped hcom fixture no longer crashed the CLI.
- Full suite passed: `pass=54 fail=0 total=54`.
- Mirror and task graph validators passed.
- Event validator reported only existing legacy warnings and `new_warnings=0`.

## Findings

No blocking findings.
