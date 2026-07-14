# Insight Record

Insight ID: INS-0013
Project: MAP
Related task: TASK-123
Detected by: claude-lab-valo
Date: 2026-07-03
Status: PROMOTED

## Short description


Emergence/Insight capture was skipped entirely for an entire project (ProjectUpdater, TASK-123-125) despite emergence/README.md already existing and defining project-level insight/idea folders - nothing in the bootstrap or task-completion process required it, so it was silently omitted until the operator asked directly.

## Trigger


Operator asked 'was there anything created by the E/I for the project updater project?' after TASK-123/124/125 were already released - the honest answer was no, nothing had been captured.

## The synthesis


PROJECT_BOOTSTRAPPING_SYSTEM.md (TASK-115) already requires research needs, risks, and decision paths at bootstrap, but never required emergence capture as an ongoing practice or a release-gate check, so a full project could ship without ever touching the Emergence system even though it existed and applied.

## Why it might matter


This is the highest-value finding from the ProjectUpdater cycle: an entire system (Emergence) can go completely unused on a real project not because it doesn't apply, but because nothing enforces checking it. Promoted directly into TASK-126 (make Emergence capture mandatory per-project, enforced via release_task.py's checklist gate) per operator directive rather than left as a passive insight.

## Evidence


Zero emergence artifacts existed tagged to ProjectUpdater before TASK-126; Projects/ProjectUpdater/ had no insights/ideas/experiments/synthesis folders at all before TASK-126.

## Risk


Making emergence capture a hard release gate could become box-ticking (a copy-pasted checklist tick with no real insight) if not paired with genuine judgment about what's worth capturing.

## Scope


MAP-system-level

## Recommended next action

Choose one:

- [x] Create follow-up task — actionable now
- [ ] Ignore — not worth preserving
- [ ] Park for later — valid but low priority
- [ ] Create idea card — needs more development
- [ ] Run small experiment — testable now
- [ ] Escalate to Human Owner / Project DRI — requires decision authority

## Notes

- Promoted directly into TASK-126 per operator directive (hcom): backfill
  ProjectUpdater's E/I records and make Emergence capture mandatory
  per-project going forward, enforced through
  `MAP_System/scripts/release_task.py`'s checklist gate rather than left
  as a documentation-only suggestion.
