# Repair Record

Repair ID: REPAIR-0002
Related task: TASK-129
Found by: claude-lab-valo
Date: 2026-07-03
Severity: DRIFT
Status: APPLIED

## What was found

A grep-based bidirectional cross-link matrix across all 11 systems built
in TASK-103–126 found 3 one-way references (a "Related files" mention in
one system's file with no reciprocal entry in the referenced file):

- `HUMAN_INTERFACE_SYSTEM.md` referenced `CONTEXT_SYSTEM.md`, but
  `CONTEXT_SYSTEM.md` did not reference it back.
- `RISK_SYSTEM.md` referenced `RESEARCH_SYSTEM.md`, but `RESEARCH_SYSTEM.md`
  did not reference it back.
- `PROJECT_BOOTSTRAPPING_SYSTEM.md` referenced `CONTEXT_SYSTEM.md`, but
  `CONTEXT_SYSTEM.md` did not reference it back.

## Surfaced by

Operator concern (hcom #22305) that the 11 systems may not be genuinely
cross-linked as "one base." Manual grep matrix run during TASK-129
(MAP System Adherence Audit), spot-checking ahead of TASK-131's fuller
tooling pass.

## Severity rationale

`DRIFT`: each gap was a missing backlink in an otherwise-correct system,
not a broken reference or contradictory content. Nothing was blocked;
the systems still functioned independently, they just weren't fully
bidirectionally discoverable.

## Proposed or applied fix

Added the missing backlink bullets to each target file's "Related files"
section:

- `CONTEXT_SYSTEM.md` now links to `HUMAN_INTERFACE_SYSTEM.md` and
  `PROJECT_BOOTSTRAPPING_SYSTEM.md`.
- `RESEARCH_SYSTEM.md` now links to `RISK_SYSTEM.md`.

## Authority check

- [x] DRIFT or mechanical BLOCKING — core agent applied directly
- [ ] Judgment-requiring BLOCKING — proposed via hcom before applying
- [ ] STRUCTURAL — proposed to command-center, not yet applied without approval

## Verification

- Re-ran the bidirectional grep matrix across all 11 systems after the
  fix: 0 remaining one-way gaps.
- TASK-131 (codex-lab-dino) is building a reusable, tooled version of
  this check independently, to confirm and make this repeatable rather
  than a one-off manual grep.

## Recurrence check

- [x] First occurrence of this drift class
- [ ] Repeat — logged in `shared/improvement-backlog.md`: N/A
- [ ] Repeat — permanent fix proposed (validator/template/decision): see
  TASK-131 — if it lands as a script, it should be wired into the health
  check suite in `SELF_REPAIR_SYSTEM.md`/`repairs/README.md` so this
  doesn't require a manual grep matrix next time.

## Notes

This is the first concrete evidence supporting the operator's concern
(hcom #22305): the systems were individually well-built but not
verified as cross-linked as a whole until this audit checked directly
rather than assumed from memory.
