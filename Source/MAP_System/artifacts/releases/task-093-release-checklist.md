# Release Checklist: TASK-093

## Header

```text
task_id:      TASK-093
released_by:  codex-lab-lema
release_date: 2026-07-02
review_record: MAP_System/artifacts/reviews/task093-review-lema.md
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared

## Summary

TASK-093 is ready to release: CommandCenterUI now supports quote/reply
round-trips through hcom `reply_to`, renders quote context without changing the
source hcom record, and adds a client-side needs-attention inbox backed by a
read-only `/api/attention` endpoint.

## Verification

```text
node --check chat.js: pass
server.py AST parse: pass
GET /api/chat quote context: pass
GET /api/attention: pass
POST /api/attention: 404 as expected
bad reply_to validation: pass
cross-origin chat send rejection: pass
```
