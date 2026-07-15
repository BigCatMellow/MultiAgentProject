<!-- hpom: file: artifacts/releases/task-195-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-195

## Header

```
task_id:      TASK-195
released_by:  codex-lab-nivo
release_date: 2026-07-15
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-195 hardens the RnS watcher after the 4:11 AM live failure. The watcher
no longer dies when `hcom r` times out, failed recorded-reset nudges are not
consumed as success, retry backoff is tracked in `failed_nudges`, and live
hcom sessions are reconciled out of stale `standby/out_of_tokens` durable
state. CommandCenterUI RnS health now distinguishes missing, stale, wrong, and
live watcher pidfile states.

- Shared files: `MAP_System/scripts/limit_watcher.py`,
  `MAP_System/tests/test_limit_watcher.py`, and the live recovery update to
  `MAP_System/agents/status.json`.
- CommandCenterUI: `/home/home/Projects/CommandCenterUI/app/server.py` contains
  the watcher-health hunk reviewed for this task. Reviewers separately flagged
  unrelated working-tree changes in that file; those need their own commit/task
  boundary and are not claimed as TASK-195 release scope.
- Decisions: no new MAP policy decision; this is a bug fix to the existing
  RnS contract.
- Follow-ups: no new task needed for the watcher behavior. The commit-boundary
  warning for CommandCenterUI is recorded here and in the review artifacts.
- Events: the 4:11 failure, live repair, approval, and this release are
  recorded in `events/events.jsonl`.
- Emergence: considered. The lesson is operational and already folded into
  the RnS implementation and tests; no separate emergence artifact is needed.

## Verification

- `MAP_System/tests/test_limit_watcher.py`: 28/28 pass.
- `MAP_System/scripts/validate_events.py --fail-on-new`: pass.
- `MAP_System/tests/test_validate_layer1.py`: pass.
- `MAP_System/scripts/validate_task_graph.py`: pass.
- `MAP_System/scripts/validate_task_mirrors.py`: pass.
- Independent reviews: `artifacts/reviews/task195-review-zera.md` and
  `artifacts/reviews/task195-review-toku.md`.
