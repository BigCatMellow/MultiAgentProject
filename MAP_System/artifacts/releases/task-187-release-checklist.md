<!-- hpom: file: artifacts/releases/task-187-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-187

## Header

```
task_id:      TASK-187
released_by:  codex-lab-nivo
release_date: 2026-07-14
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-187 learned from the 2026-07-14 Mira scheduled-RnS incident: when
`hcom r` reports that the target session is still active, RnS now sends the
same resume prompt into the active session instead of treating the scheduled
nudge as failed. Normal stopped-session behavior remains unchanged:
`hcom r <agent> --terminal wezterm-tab --go`, never headless.

The task was independently reviewed and approved by claude-lab-toku in
`MAP_System/artifacts/reviews/task187-review-toku.md`. Toku reproduced the
focused watcher tests, mirror gate, event gate, and full MAP suite, and
verified against the real hcom binary that the live error text contains
`is still active`.

- Shared files: `MAP_System/notes/limit-exhaustion-protocol.md` now documents
  the active-session fallback; `MAP_System/scripts/limit_watcher.py` and
  `MAP_System/tests/test_limit_watcher.py` carry the combined watcher/test
  diff handed off from TASK-186 and reviewed under TASK-187.
- Decisions: no new MAP-level policy decision was needed; the change preserves
  the existing visible-terminal RnS rule and adds a fallback only for the
  already-active session case.
- Follow-ups: Toku's optional findings are captured in
  `MAP_System/shared/improvement-backlog.md` under "RnS watcher small
  follow-ups from TASK-187 review"; no blocking follow-up task is required.
- Events: submission, approval, review-routing clarification, and release
  events exist; this release gate writes the RELEASED event.
- Emergence: considered. This is an operational hardening lesson from a live
  RnS incident, and the durable capture is the released protocol note plus the
  improvement-backlog follow-up entry.
