<!-- hpom: file: artifacts/releases/task-204-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-204

## Header

```
task_id:      TASK-204
released_by:  gune
release_date: 2026-07-15
reviewed_by:  claude-lab-toku
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-204 adds an OPTIONAL, opt-in "debate pre-escalation" step to MAP's
conflict-freeze / decision-authority path, using the already-shipped
`hcom run debate` workflow. Doc + convention only; additive and non-breaking.

- Files: `MAP_System/DECISION_AUTHORITY_SYSTEM.md` (new "Optional: debate
  pre-escalation" subsection) and `MAP_System/notes/review-guide.md` (new
  "When to Invoke Debate" section).
- Decisions: no decision record changed. Debate remains opt-in and does not
  gate or replace any existing escalation path; `scripts/flag_conflict.py`
  behavior is unchanged.
- Follow-ups: none required. Promoted from IDEA-0019 via PROMO-0009 (operator
  direction-approved). Sibling ideas IDEA-0018 (eval discipline) and IDEA-0020
  (two-pizza metrics) remain CANDIDATE for future promotion.
- Events: submission, approval, and release recorded in `events/events.jsonl`.
- Emergence: considered — this task IS the promotion of IDEA-0019; no new
  artifact needed.

## Review

- Verdict: APPROVED — `artifacts/reviews/task204-review-toku.md`
  (claude-lab-toku). All 3 acceptance criteria verified; opt-in framing
  confirmed in both files; `flag_conflict.py` empty diff; `hcom run debate`
  confirmed real; no forbidden-scope edits.
- Reviewer cosmetic note (non-blocking, considered): the
  `DECISION_AUTHORITY_SYSTEM.md` `last_verified` header was not bumped. That
  file is not gated by `validate_shared_state.py`, so it does not block
  release; left as-is to keep the released artifact identical to the reviewed
  one.

## Verification

- Implementer: helper `soho` (Haiku), scoped draft under owner `gune`.
- `MAP_System/scripts/validate_task_mirrors.py`: pass.
- `python3 MAP_System/scripts/map_emergence.py validate`: OK (54 checked).
- Scope check: `git status` confirms only the two in-scope files changed by
  this task.
