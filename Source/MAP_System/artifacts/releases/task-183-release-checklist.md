<!-- release_meta: task_id: TASK-183 released_by: codex-lab-nivo -->
<!-- hpom: file: artifacts/releases/task-183-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-183

## Header

```
task_id:      TASK-183
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

TASK-183 released deterministic historical emergence compaction. The new
`map_emergence.py compact` command supports dry-run by default, explicit
`--apply`, named targets, `--all-active`, status-based closed-record skipping,
and idempotent compacting of already converted records. Active emergence
records were compacted or verified without local-model semantic drift. The task
was independently reviewed and approved by claude-lab-mira in
`MAP_System/artifacts/reviews/task183-review-mira.md`.

- Shared files: `MAP_System/shared/current-state.md` records that all active
  emergence records are converted and that `map_emergence.py compact` is now
  available for future prose records.
- Decisions: no new MAP-level decision was required; the deterministic approach
  follows directly from TASK-181 evidence that local helpers are not reliable
  enough for unsupervised canonical rewrites.
- Follow-ups: no new task filed. The operator's emergence compaction complaint
  is closed end-to-end by TASK-180, TASK-181, and TASK-183.
- Events: submission and approval events exist; this release gate writes the
  RELEASED event.
- Emergence: considered. The deterministic-transform pattern is documented in
  `MAP_System/artifacts/planning/emergence-deterministic-compaction-report.md`
  and `MAP_System/shared/current-state.md`; no additional insight record was
  needed.
