# Release Checklist: TASK-144

## Header

```text
task_id:      TASK-144
released_by:  codex-lab-veto
release_date: 2026-07-04
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-144 is ready to release. It completed the requested MAP renewal pass with
a verified full backup, a structural/process assessment, launcher path cleanup,
canonical-path validator expansion, event-warning baseline guidance updates,
LangGraph dependency bounds from TASK-145 research, stale backlog cleanup, and
INS-0016 capture.

No new decision was needed. Follow-up handling is recorded in the assessment and
backlog: `MapSqliteSaver.delete_thread()` remains low priority until MAP uses
thread-lifecycle cleanup, and the review's non-blocking note on triaging
INS-0016 is deferred rather than mutating reviewed artifacts after approval.
