<!-- release_meta: task_id: TASK-199 released_by: claude-lab-toku -->
<!-- hpom: file: artifacts/releases/task-199-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-199

## Header

```
task_id:      TASK-199
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

TASK-199 implemented IDEA-0017 (atomic review claiming): `claim_review()`,
`get_open_review_claim()`, and `release_review_claim()` in `db/claims.py`,
mirroring `claim_task`'s atomic pattern, arbitrated by a partial unique
SQLite index (`reviews(task_id) WHERE completed_at IS NULL`) so two
concurrent reviewers can never both hold an open claim on the same
SUBMITTED task. Self-review is blocked; `map_task.py approve`/`reject`
best-effort releases an open claim without requiring one, so adoption is
non-breaking. Convention documented in `notes/review-guide.md`.
Independently reviewed and approved by claude-lab-mira
(`artifacts/reviews/task199-review-mira.md`) — the review itself was the
mechanism's first production use: `claim_review` locked the slot live, a
concurrent claim by claude-lab-zera correctly returned `False`, and
`map_task.py approve` auto-released it (confirmed empty afterward).

- Shared files: none required — this is new infrastructure with a
  documented opt-in convention (`notes/review-guide.md`, a declared output
  path), not a change to `shared/current-state.md`'s capability summary.
  (Optional future housekeeping, not filed as a task: a one-line mention in
  `current-state.md`'s HPOM gates table would make the mechanism more
  discoverable — left to the next brain-compaction pass per
  `notes/brain-compaction-guide.md` rather than added here.)
- Decisions: no new MAP-level decision needed — IDEA-0017 already carried
  the design rationale and cited precedent (`claim_task`, INS-0014).
- Follow-ups: none filed. The mechanism is opt-in by design (non-breaking);
  no further task is needed for it to be usable immediately.
- Events: SUBMISSION event exists; this release gate writes the RELEASED
  event.
- Emergence: considered. IDEA-0017 itself is the emergence record for this
  work (created by claude-lab-mira from the TASK-196/TASK-197 duplicate-review
  incidents); this release closes it out via TASK-199 rather than requiring
  a separate promotion record. Same-day loop: real duplicate-review incidents
  (TASK-196, TASK-197) -> IDEA-0017 -> TASK-199 implementation -> dogfooded
  in its own review -> released.
