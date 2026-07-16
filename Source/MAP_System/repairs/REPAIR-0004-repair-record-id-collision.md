# Repair Record

Repair ID: REPAIR-0004
Related task: TASK-129
Found by: claude-lab-valo
Date: 2026-07-03
Severity: DRIFT
Status: APPLIED

## What was found

Two distinct repair records both claimed `REPAIR-0001`:

- `REPAIR-0001-runner-released-dependency-drift.md` (codex-lab-dino, tied
  to TASK-116)
- `REPAIR-0001-risk-validator-placeholder-regex-false-positive.md`
  (claude-lab-valo, tied to TASK-120)

Both agents independently numbered their first repair `0001` because
`repairs/` has no atomic ID-allocation mechanism, unlike
`scripts/map_task.py create --task-id auto` (SQLite write-locked) and
`scripts/map_emergence.py` (allocates the next insight/idea/etc. ID). This
is exactly the collision class those two tools were built to prevent —
`repairs/` was never given the same treatment.

## Surfaced by

Cross-referencing repair records while assembling the TASK-129 MAP System
Adherence Audit (operator concern, hcom #22305) and noticing muva's
`task-130-map-systems-real-usage-evidence.md` and my own
`HEALTH-0001-map-system-self-application-review.md` both cited a file
named `REPAIR-0001-risk-validator-*` that, on inspection, was a second,
unrelated `REPAIR-0001`.

## Severity rationale

`DRIFT`: the collision caused no functional failure (each file was still
individually readable and correct), but it silently broke the assumption
that a `REPAIR-NNNN` ID uniquely identifies one repair — a future
cross-reference by bare ID alone ("see REPAIR-0001") would be ambiguous.

## Proposed or applied fix

- Renamed `REPAIR-0001-risk-validator-placeholder-regex-false-positive.md`
  to `REPAIR-0003-risk-validator-placeholder-regex-false-positive.md`
  (dino's TASK-116 repair predates mine chronologically by task number,
  so it keeps `0001`; `REPAIR-0002` was already mine and unaffected).
  Updated the file's own `Repair ID:` field and the one live cross-reference
  in `HEALTH-0001-map-system-self-application-review.md`.
- Did not edit `artifacts/reviews/task120-review-dino.md` (a historical,
  already-approved review record) — that reference is left as-is per
  `ARCHIVE_RETENTION_SYSTEM.md`'s rule against rewriting completed history;
  a reader following it will still find the correct content, just under
  its current filename.
- Flagged the same stale reference in `task-130-map-systems-real-usage-evidence.md`
  to codex-lab-muva/lema via hcom rather than editing another agent's
  currently-under-review task output directly.

## Root-cause fix (not yet applied — proposing, not building unilaterally)

`repairs/` needs the same atomic-ID-allocation treatment `map_task.py`
and `map_emergence.py` already have, or this will recur. Recommending a
follow-up task: add a `--repair-id auto` (or equivalent) mode to a small
`map_repair.py` helper, or extend an existing script, so two agents
filing a repair concurrently cannot both land on the same number. Not
built here to keep this repair's own scope mechanical; logged in
`shared/improvement-backlog.md`.

## Authority check

- [x] DRIFT or mechanical BLOCKING — core agent applied directly
- [ ] Judgment-requiring BLOCKING — proposed via hcom before applying
- [ ] STRUCTURAL — proposed to command-center, not yet applied without approval

## Verification

- `ls MAP_System/repairs/` shows four uniquely-numbered records
  (`REPAIR-0001` through `REPAIR-0004`, `HEALTH-0001`), no duplicates.
- `grep -rn "^Repair ID:" MAP_System/repairs/*.md` shows each ID appears
  exactly once.

## Recurrence check

- [ ] First occurrence of this drift class
- [x] Repeat — logged in `shared/improvement-backlog.md`: see entry added
  by this repair
- [x] Repeat — permanent fix proposed (validator/template/decision): a
  `map_repair.py` ID-allocation helper, not yet built

## Notes

This is itself a direct instance of the operator's concern (hcom #22305):
two systems (task claiming, emergence) got proper tooling; a third
(repairs) that clearly needed the same treatment did not, and the gap
went unnoticed until this audit checked cross-references directly rather
than assuming consistency.
