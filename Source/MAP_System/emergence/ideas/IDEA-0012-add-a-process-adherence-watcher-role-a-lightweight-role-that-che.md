# Idea Card

Idea ID: IDEA-0012
Project: MAP
Source insight or synthesis: NONE
Owner: claude-lab-valo
Date: 2026-07-02
Status: PROMOTED_TO_TASK

## Idea


Add a Process-Adherence Watcher role: a lightweight role that checks in-flight tasks against HPOM/AGENTS.md process (task claiming, review gates, event logging, no-self-review) and flags drift, rather than relying on each agent to self-audit.

## Problem or opportunity


Nothing currently watches whether agents actually follow HPOM/review/event-logging process in real time; drift is only caught retrospectively via review or gap reviews like MAP_repo_systems_gap_review.md.

## Why now


Operator explicitly floated this idea (hcom #19306) while directing Research System build; capturing now before it gets lost.

## Expected benefit


Could reduce process drift, catch missed events/review gates earlier, and feed the future Retrospective System.

## Cost


Another running role/session to coordinate; risk of becoming noisy or duplicating review gates if not scoped tightly.

## Reversibility

Can this be undone easily?

- [ ] Yes
- [ ] No
- [ ] Partially — explain: TBD

## Smallest safe experiment


Create and validate file-backed emergence records.

## Decision needed

Who must approve this before it can be promoted?

- [ ] Task DRI — within current task scope
- [ ] Review DRI — requires review gate
- [ ] State Steward — changes shared state
- [ ] Project DRI — changes project direction
- [ ] Human Owner — changes MAP-level rules or governance

## Recommendation

- [ ] Park — valid but not the right time
- [ ] Reject — not worth pursuing
- [ ] Test — run the smallest safe experiment
- [x] Promote to task — evidence is sufficient, ready for HPOM

Promoted via `PROMO-0007` (approved by command-center instruction, hcom
#22305) into `TASK-129` (MAP System Adherence Audit), where
claude-lab-valo held the bounded Process-Adherence Steward role for one
audit cycle rather than as a new permanent agent identity.
