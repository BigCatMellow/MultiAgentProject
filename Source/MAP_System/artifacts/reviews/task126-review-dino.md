# Review Record: TASK-126

## Header

```text
task_id:      TASK-126
reviewer:     codex-lab-dino
review_date:  2026-07-03
task_owner:   claude-lab-valo
```

Reviewer != owner. Independence check passes.

## Verdict

```text
APPROVED
```

## Acceptance Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Projects/ProjectUpdater has real INS/IDEA records for what was learned during TASK-123-125, using map_emergence.py | PASS | `INS-0011`, `INS-0012`, `INS-0013`, and `IDEA-0015` exist under `MAP_System/emergence/`, are indexed in `INDEX.md`, validate cleanly, and are tagged to `ProjectUpdater` where applicable. `Projects/ProjectUpdater/{insights,ideas,experiments,synthesis}/README.md` explains the canonical CLI storage path. |
| 2 | Bootstrap docs require emergence folder creation and ongoing capture as work proceeds | PASS | `PROJECT_BOOTSTRAPPING_SYSTEM.md` adds Emergence capacity as the seventh pre-first-task requirement and a separate ongoing capture section. `NEW_PROJECT_WIZARD.md` adds folder creation at step 7 and per-task capture consideration at step 9. |
| 3 | release_task.py mechanically requires an `Emergence capture considered` checklist line before release, with a passing focused test | PASS | `scripts/release_task.py` adds `emergence capture considered` to `REQUIRED_CHECKS` with an exact completed-checkbox regex. `templates/release-checklist.md` includes the line. `tests/test_release_gate.py::test_missing_emergence_line_blocks_release` passes, and the full suite passes 33/33. |
| 4 | shared/decisions.md records this as a POLICY-class decision | PASS | `DEC-026` records the operator-directed policy decision, affected files, and enforcement behavior. |
| 5 | events/events.jsonl has PROGRESS/SUBMISSION entries tracing the work | PASS | `map_task.py log TASK-126` shows PROGRESS and SUBMISSION events with relevant artifact paths. `validate_events.py` reports 0 errors and the known 33 historical warnings. |

## Files Reviewed

- `MAP_System/tasks/TASK-126.json`
- `MAP_System/scripts/release_task.py`
- `MAP_System/tests/test_release_gate.py`
- `MAP_System/templates/release-checklist.md`
- `MAP_System/PROJECT_BOOTSTRAPPING_SYSTEM.md`
- `MAP_System/NEW_PROJECT_WIZARD.md`
- `MAP_System/CHANGE_CONTROL_SYSTEM.md`
- `MAP_System/emergence/README.md`
- `MAP_System/emergence/INDEX.md`
- `MAP_System/emergence/insights/INS-0011-no-headless-browser-was-preinstalled-for-verifying-static-html-a.md`
- `MAP_System/emergence/insights/INS-0012-feature-completeness-gaps-a-missing-ui-filter-missing-accessibil.md`
- `MAP_System/emergence/insights/INS-0013-emergence-insight-capture-was-skipped-entirely-for-an-entire-pro.md`
- `MAP_System/emergence/ideas/IDEA-0015-add-an-export-import-json-button-to-projectupdater-to-mitigate-i.md`
- `Projects/ProjectUpdater/insights/README.md`
- `Projects/ProjectUpdater/ideas/README.md`
- `Projects/ProjectUpdater/experiments/README.md`
- `Projects/ProjectUpdater/synthesis/README.md`
- `MAP_System/shared/current-state.md`
- `MAP_System/shared/decisions.md`

## Findings

No blocker or required findings.

## Review Notes

- The central `MAP_System/emergence/` record location is consistent with the current `map_emergence.py` implementation. The ProjectUpdater folders are intentionally present as project capacity and explain that CLI-created records are stored centrally with `Project: ProjectUpdater` metadata.
- The release gate now requires five completed checklist lines: the four existing checked lines plus `Emergence capture considered`. Some prose still refers to "existing 3" items, but the behavioral path, template, and tests are aligned.
- `IDEA-0015` remains a candidate idea, not an authorized scope expansion; it is correctly captured without changing ProjectUpdater behavior in TASK-126.

## Forbidden Changes

- PASS: The task does not implement the ProjectUpdater export/import idea; it only captures it for future promotion.
- PASS: The release gate blocks only missing checklist consideration and does not force creation of low-value Emergence artifacts.
- PASS: No unrelated ProjectUpdater app files were changed as part of the policy backfill.
- PASS: Existing released task records are not mutated retroactively; enforcement applies through future `release_task.py` runs.

## Verification

```bash
MAP_System/.venv/bin/python MAP_System/scripts/map_emergence.py validate
MAP_System/.venv/bin/python MAP_System/tests/test_release_gate.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py
MAP_System/scripts/run_tests.sh
```

Results:

```text
emergence validation: PASS, 35 checked
release gate focused tests: PASS
task graph: PASS
events: errors=0 warnings=33 historical warnings
full MAP suite: PASS, 33/33
```
