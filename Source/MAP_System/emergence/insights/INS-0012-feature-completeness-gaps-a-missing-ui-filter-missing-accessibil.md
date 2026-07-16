# Insight Record

Insight ID: INS-0012
Project: ProjectUpdater
Related task: TASK-123
Detected by: claude-lab-valo
Date: 2026-07-03
Status: PROMOTED

## Short description


Feature-completeness gaps (a missing UI filter, missing accessibility semantics) were caught by independent reviewers rather than by self-checking acceptance criteria line-by-line before submission.

## Trigger


TASK-123's review (codex-lab-dino) found requirements.md explicitly listed an Archived filter that the implementation's UI omitted, even though a code branch for it already existed. TASK-124's audit (codex-lab-lema) found labels/ARIA gaps that a stricter self-check against WCAG-adjacent basics could have caught before submission.

## The synthesis


Both gaps were things a line-by-line pass of shared/requirements.md against the built UI, or a basic accessibility pass, would have caught pre-submission - they were not subtle bugs, they were completeness gaps against already-written requirements.

## Why it might matter


This is the same shape of failure as RETRO-0001's output_paths pattern (MAP_System/RETROSPECTIVE_SYSTEM.md) but applied to feature completeness instead of MAP process compliance: a written requirement existed, but nothing forced a systematic check against it before submission.

## Evidence


artifacts/reviews/task123-review-dino.md (missing Archived filter); artifacts/accessibility-audit-lema.md (missing labels/ARIA).

## Risk


If generalized into a mandatory pre-submission checklist, could become box-ticking ceremony rather than genuine review, especially for small tasks.

## Scope


MAP-system-level improvement (a pre-submission completeness-check habit), discovered during a ProjectUpdater task

## Recommended next action

Choose one:

- [ ] Ignore — not worth preserving
- [x] Park for later — valid but low priority
- [ ] Create follow-up task — actionable now
- [ ] Create idea card — needs more development
- [ ] Run small experiment — testable now
- [ ] Escalate to Human Owner / Project DRI — requires decision authority

## Notes

- Same shape of failure as RETRO-0001 (`MAP_System/RETROSPECTIVE_SYSTEM.md`)
  applied to feature completeness instead of MAP process compliance.
  Parked rather than turned into a new mandatory gate right now, since
  RETRO-0001's follow-up-prevention discipline already covers "recurring
  pattern → propose a permanent fix" at the next retrospective cycle;
  revisit there if this recurs a third time.
