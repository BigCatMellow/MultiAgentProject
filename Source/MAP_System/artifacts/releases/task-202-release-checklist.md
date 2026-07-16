<!-- release_meta: task_id: TASK-202 released_by: claude-lab-toku -->
<!-- hpom: file: artifacts/releases/task-202-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-202

## Header

```
task_id:      TASK-202
released_by:  claude-lab-toku
release_date: 2026-07-15
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-202 (Wave 3 TOKU lane) added durable operator-identity and hcom-intent
conventions, unlocking calibration parameter 7 and the P1-practice grade
that `map-real-parameter-calibration-results-2026-07-14.md` had flagged
missing-data: `shared/operator-identities.md` + `agents/operator-identities.json`
name `bigboss` (direct terminal) and `command-center` (CommandCenterUI's
`OPERATOR_NAME` relay) as operator identities with concrete evidence, cross-
linked from `agents/README.md`; `notes/communication-architecture.md`
documents that hcom intent lives only in hcom's own DB (`session_replay.py`
has zero hcom ingestion, correcting the original work packet's premise) with
a verified-working query example; a new addendum in the calibration results
artifact gives runnable queries and real smoke-test numbers for both
parameters. Independently reviewed by codex-lab-nivo: first pass found a
real contradiction (the doc claimed every hcom message carries intent, but
the measurement showed roughly half unset) — fixed and re-reviewed,
APPROVED (`artifacts/reviews/task202-review-nivo.md`,
`artifacts/reviews/task202-rereview-nivo.md`).

- Shared files: `shared/operator-identities.md` is a new shared file
  (declared output path, hpom-headed, passes `validate_shared_state.py`
  at 22/22). No change to `shared/current-state.md` was needed — this is
  new reference infrastructure, not a runtime capability change.
- Decisions: no new MAP-level decision needed.
- Follow-ups: none filed. The addendum's honest-negative finding (operator
  approval load's *gated* half — `needs_approval` event coverage — remains
  unmeasurable until Wave 3/8 infrastructure lands) is documented in place
  rather than spun into a placeholder task.
- Events: SUBMISSION events exist for both the original submission and the
  post-rework resubmission; this release gate writes the RELEASED event.
- Emergence: considered. This task closed a measurement gap the calibration
  report itself named rather than surfacing a new insight; no separate
  emergence record needed beyond the calibration addendum itself.

## Rework Note

First review round returned `CHANGES_REQUESTED` (real, valid finding — a
genuine contradiction between claimed and measured behavior, not a false
positive). Fixed via `map_task.py rework` → reclaim → wording fix →
resubmit → re-review → `APPROVED`. A local Ollama helper (gemma3:4b) drafted
a candidate wording fix per operator direction to route low-risk rewrites to
lower-level helpers; its output had raw terminal-control artifacts embedded
and was not used directly — the final wording was written fresh, informed by
the helper's direction and the reviewer's required-change text.
