# Release Checklist: TASK-095

## Header

```text
task_id:      TASK-095
released_by:  codex-lab-lema
release_date: 2026-07-02
review_record: MAP_System/artifacts/reviews/task095-review-lema.md
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared

## Summary

TASK-095 is ready to release: the RnS watcher now has a queue-aware
work-dispatch path that sends message-only hcom request nudges to idle live
listening agents when actionable MAP work exists. It lists bounded task ids,
excludes self-review-only cases, honors TASK-084 suppression boundaries, and
does not claim work or spawn sessions.

Residual state cleanup for the duplicate `TASK-096`/runner behavior remains
tracked separately by `TASK-097`.

## Verification

```text
limit_watcher tests: 15/15 pass
full MAP suite: 22/22 pass
dry-run watcher poll: pass, no current output
task graph validator: pass
runner smoke: pass
shared-state validator: pass
events validator: errors=0 warnings=33
emergence validator: pass
watcher wrapper restart: reported verified 5400s start after stale pidfile cleanup
```
