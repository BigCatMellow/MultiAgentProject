<!-- release_meta: task_id: TASK-184 released_by: codex-lab-nivo -->
<!-- hpom: file: artifacts/releases/task-184-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-184

## Header

```
task_id:      TASK-184
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

TASK-184 made `command_center_intake.py` the default visible path for broad
operator directives. `AGENTS.md` now documents the convention and urgent
live-control exemption, and the intake wrapper can optionally post the
validated packet as `hcom --intent inform` with `--hcom-inform-to` before
decomposition. The task was independently reviewed and approved by
claude-lab-mira in `MAP_System/artifacts/reviews/task184-review-mira.md`.

- Shared files: `MAP_System/AGENTS.md` now records the broad-directive intake
  convention.
- Decisions: no new MAP-level decision was needed; this is an operating
  convention for the already-built command-center intake path.
- Follow-ups: no new task filed. Mira's non-blocking review note is accepted:
  callers should pass a registered `--hcom-name` such as the active agent's
  hcom name when using `--hcom-inform-to`.
- Events: submission and approval events exist; this release gate writes the
  RELEASED event.
- Emergence: considered. This is process adoption for an existing command
  surface; no new insight beyond TASK-175's already-recorded recommendation.
