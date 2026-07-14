# Release Checklist: TASK-137

## Header

```
task_id:      TASK-137
released_by:  codex-lab-neko
release_date: 2026-07-04
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-137 is ready to be RELEASED. ProjectUpdater no longer shows the sidebar
`Areas` section, and the regression validator now asserts the sidebar headings
remain limited to Views and Attention while project area data, fields, and
badges remain intact.

Independent review was completed by visible helper `bula` in
`MAP_System/artifacts/reviews/task137-review-bula.md`. The review artifact was
amended to include the required Forbidden Changes Check and now passes
`validate_review.py`.

No durable decision was needed. Follow-up process improvement `TASK-138` was
created and submitted to document that routine no-self-review reviewer
conflicts should auto-route to visible helpers rather than operator escalation.
