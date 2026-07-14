<!-- hpom: file: artifacts/releases/task-182-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-182

## Header

```
task_id:      TASK-182
released_by:  claude-lab-mira
release_date: 2026-07-14
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-182 brought external CommandCenterUI current with the MAP runtime built
in TASK-171–179: a read-only `GET /api/map/health` endpoint (runner route,
librarian wikilink validation, session-replay index health, RnS watcher
state; per-source error isolation; 20s TTL cache; parallel source fetch) and
a "MAP runtime" sidebar card in the chat UI. Independently reviewed and
APPROVED by codex-lab-nivo (`artifacts/reviews/task182-review-nivo.md`),
including a monkeypatch verification of cache behavior and per-source error
rows.

- Shared files: `shared/current-state.md` updated (CommandCenterUI currency
  capability bullet; RnS stale-incident known-health-issue naming IDEA-0009's
  experiment as the ready next step); validate_shared_state passes 21/21.
- Decisions: no new MAP-level decision needed — the operator's lead
  assignment (hcom #33409) and "get it done and implemented as needed"
  directive are cited in the task record as the output-boundary approval
  TASK-175 required; the external repo edit is recorded in the task's
  output_paths and in two CommandCenterUI commits (baseline `bb847f6`,
  task `01a3435`, local only — push awaits operator go-ahead).
- Follow-ups: no new task filed deliberately — the RnS warn's fix is already
  tracked (IDEA-0009 dry-run suppression experiment, marked ready-to-run by
  TASK-146); optional `/app.html` card parity is noted in the task artifact
  as an operator-choice follow-on, not queued as work.
- Events: SUBMISSION event logged with trace fields; RELEASED event written
  by this release gate.
- Emergence: considered — the live-call-caught-two-bugs finding reinforces
  the already-promoted INS-0016 (validator/live-surface coverage) and is
  cross-referenced in `artifacts/command-center-ui/task-182-map-health-cards.md`
  rather than duplicated as a new insight.
