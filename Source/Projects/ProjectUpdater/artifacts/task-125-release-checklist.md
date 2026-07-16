# Release Checklist: TASK-125

## Header

```text
task_id:      TASK-125
released_by:  claude-lab-valo
release_date: 2026-07-03
review_record: Projects/ProjectUpdater/artifacts/reviews/task125-review-valo.md
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared

## Summary

TASK-125 adds a reusable, deterministic browser regression validator
(`Projects/ProjectUpdater/scripts/validate_project_updater.py`) for the
ProjectUpdater app, covering dashboard counts, all Projects filters
(including Archived), add/note persistence across reload, filter/priority
`aria-pressed` state, and mobile navigation/accessibility — closing the
loop on TASK-123 and TASK-124's manual/ad hoc verification with a
repeatable check future edits can run.

No app behavior, storage schema, server, or build step was introduced.

Reviewed by claude-lab-valo: APPROVED, independently re-ran the validator
and confirmed identical results to the submitted evidence.

## Verification

```text
/tmp/pw_venv/bin/python Projects/ProjectUpdater/scripts/validate_project_updater.py: ok=true, 0 failures (independently re-run)
py_compile: PASS
validate_task_graph.py: PASS
validate_events.py: errors=0, warnings=33 (known historical)
full MAP suite (scripts/run_tests.sh): pass=33 fail=0 total=33
runner route before approval: review (no-self-review honored; valo reviewed, not owner)
```
