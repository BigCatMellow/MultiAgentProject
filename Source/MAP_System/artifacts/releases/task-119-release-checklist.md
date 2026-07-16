# Release Checklist: TASK-119

## Header

```text
task_id:      TASK-119
released_by:  codex-lab-lema
release_date: 2026-07-03
review_record: MAP_System/artifacts/reviews/task119-review-lema.md
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared

## Summary

TASK-119 is ready to release: Rise & Shine now detects expired
`IN_PROGRESS` claims even when the runner has no `READY` work, then sends a
throttled request-format nudge to the stale claim owner with resume, submit,
release/rework, or intentional-pause options.

No durable decision entry was needed; this is an operator-requested repair to
the live RnS behavior after the TASK-117 stale-claim stall.

## Verification

```text
independent review: APPROVED by codex-lab-lema
focused limit_watcher: PASS, 16 tests
py_compile: PASS
task graph: PASS
events: errors=0 warnings=33 historical warnings
shared state: 18 checked, 0 failures, 0 warnings
full MAP suite: pass=33 fail=0 total=33
```
