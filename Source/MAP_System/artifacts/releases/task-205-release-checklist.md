<!-- hpom: file: artifacts/releases/task-205-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-205

## Header

```
task_id:      TASK-205
released_by:  gune
release_date: 2026-07-15
reviewed_by:  claude-lab-zera
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-205 adds a separate full-fidelity ProjectUpdater backup export/import
flow to close the practical localStorage data-loss mitigation gap from
IDEA-0015 / DEC-028's first software-delivery slice.

- Files: `Projects/ProjectUpdater/app/index.html` and
  `Projects/ProjectUpdater/artifacts/task-projectupdater-backup-verification.md`.
- Shared files: no shared MAP policy/state files required changes for this
  project-app slice.
- Decisions: no new decision record required; this implements the already
  authorized DEC-028 / TASK-205 scope.
- Follow-ups: none required. The independent review found no blocking issues
  or residual follow-up work.
- Events: submission, approval, and Gune's release are recorded in
  `events/events.jsonl`.
- Emergence: considered. No new emergence card needed; the task is the
  implementation of the existing data-loss mitigation idea rather than a new
  insight.

## Review

- Verdict: APPROVED — `MAP_System/artifacts/reviews/task205-review-zera.md`
  by `claude-lab-zera`.
- The reviewer used an independent Node/vm harness against the real
  `index.html` script and verified round-trip restore, confirm-decline guard,
  parse-error handling, wrong-shape JSON handling, and that `exportStatus()`,
  `STORE_KEY`, and the schema were untouched.

## Verification

- Implementer verification artifact:
  `Projects/ProjectUpdater/artifacts/task-projectupdater-backup-verification.md`.
- Round trip restored the original full model exactly, including
  `id`, `goal`, `nextAction`, `points`, `streak`, `reminderDays`,
  `lastVisited`, and `dueDate`.
- Malformed JSON left `localStorage["projectUpdater.v1"]` byte-identical.
- `MAP_System/scripts/validate_task_mirrors.py`: pass.
- `MAP_System/scripts/validate_task_graph.py`: pass.
- `MAP_System/scripts/validate_task_schema.py`: pass.
- `MAP_System/scripts/validate_events.py --fail-on-new`: pass with only
  pre-existing legacy warnings.
