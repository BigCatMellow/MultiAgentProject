# Release Checklist: TASK-133

## Header

```text
task_id:      TASK-133
released_by:  codex-lab-dino
release_date: 2026-07-03
review_record: Projects/ProjectUpdater/artifacts/reviews/task133-review-valo.md
prepared_by:  codex-lab-dino
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-133 adds the missing ProjectUpdater project-management operations:

- edit existing projects;
- delete projects with confirmation and related-note cleanup;
- store multiple goals while preserving the legacy single `goal` field;
- store a project folder path;
- expose an `Open folder` project-card action using the stored path through
  `file://`.

The mid-task scope correction is reflected in the released implementation:
there is no Command Center Lab launch command, no `PROJECT_DIR=...` command
generation, no clipboard shell-command flow, and no backend/process execution.

No new decisions or follow-up tasks were required. Emergence capture was
considered; no new insight/idea was warranted because this was direct operator
feature work and the notable scope correction is documented in the review and
verification artifacts.

## Verification

```text
review: APPROVED by claude-lab-valo
review record validation: PASS
python py_compile validator: PASS
extracted app JS node --check: PASS
ProjectUpdater browser validator: PASS, ok=true
validate_task_graph.py: PASS
validate_events.py: errors=0 warnings=33 historical warnings
map_emergence.py stale: PASS, no findings
run_tests.sh: PASS, 33/33
```
