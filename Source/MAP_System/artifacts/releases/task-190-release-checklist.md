<!-- release_meta: task_id: TASK-190 released_by: claude-lab-zero -->
<!-- hpom: file: artifacts/releases/task-190-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-190

## Header

```
task_id:      TASK-190
released_by:  claude-lab-zero
release_date: 2026-07-14
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-190 added `scripts/cost_yield.py`, a read-only per-task cost-proxy x
outcome rollup (codeburn `yield.ts` pattern, source-mining audit item #3 /
TASK-171 Priority 2): joins events.jsonl volumes with map.db lifecycle state,
classifies released / approved_not_released / retired / abandoned /
legacy_done / in_flight, and emits the productive-vs-abandoned spend split
plus cost-per-released-output view in text and `--json`. All cost signals are
labeled proxies; no currency figures. Independently reviewed and approved by
claude-lab-mira in `MAP_System/artifacts/reviews/task190-review-mira.md`.

- Shared files: no shared/ files required changes; the deliverable is the
  script, its tests, the run_tests.sh wiring, and the report artifact
  `MAP_System/artifacts/reports/cost-yield-rollup-2026-07-14.md` — all
  registered output paths.
- Decisions: no new MAP-level decision needed. Two in-scope design calls
  (legacy_done as a separate outcome class; sibling script per the task
  record) were flagged over hcom and approved by the dispatcher before
  submission (#34179/#34199); the rationale is stated in the report artifact.
- Follow-ups: no new task filed by the owner. The rollup's operator finding
  (~37% of attributed spend parked at the release gate in APPROVED tasks) is
  going into the reviewer's operator report; acting on it is an operator
  decision, not a task this release should self-create.
- Events: SUBMISSION and APPROVED events exist; this release gate writes the
  RELEASED event.
- Emergence: considered. The release-gate-backlog visibility finding is
  captured in the report artifact and the reviewer's operator report; no
  separate emergence card needed for the tooling itself.
