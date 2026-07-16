# Release Checklist: TASK-092

## Header

```text
task_id:      TASK-092
released_by:  codex-lab-lema
release_date: 2026-07-02
review_record: MAP_System/artifacts/reviews/task092-rereview-lema.md
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared

## Summary

TASK-092 adds local Ollama-backed plain-English gists for eligible hcom agent
messages in CommandCenterUI. The rereview verified the rework that gates both
server-side summary generation and client-side gist rendering to
`sender_kind == "instance"`, preserving raw operator/system/external messages.
The feature remains read-only from the browser summary endpoint, keeps verbatim
message text one click away, and caches summaries per hcom event id.

## Verification

```text
node --check /home/home/Projects/CommandCenterUI/src/chat.js: pass
server.py ast parse: pass
GET /api/chat?limit=20: pass
GET /api/summaries?since=0: pass
POST /api/summaries: 404 as expected
validate_task_graph.py: pass
validate_events.py: errors=0 warnings=33
validate_shared_state.py: pass
```
