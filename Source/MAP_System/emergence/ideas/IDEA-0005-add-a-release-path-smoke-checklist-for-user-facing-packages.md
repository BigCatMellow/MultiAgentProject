# Idea Card

Idea ID: IDEA-0005
Project: MAP
Source insight or synthesis: MAP_System/emergence/insights/INS-0005-release-reviews-must-inspect-every-user-visible-acquisition-path.md
Owner: codex-lab-maki
Date: 2026-07-01
Status: PROMOTED

## Idea


Add a release-path smoke checklist for user-facing packages.

## Problem or opportunity


Validation focused on source scripts and missed retained archives, stale docs, and generated-download paths that users can still follow.

## Why now


The Command Center Lab is actively testing emergence workflow.

## Expected benefit


A lightweight checklist would catch stale ZIPs, contradictory README files, missing assets, and post-install verification gaps before users test on another machine.

## Cost


Small: add a reusable checklist template and require it only for tasks that publish installers, scripts, archives, or desktop launchers.

## Reversibility

Can this be undone easily?

- [ ] Yes
- [ ] No
- [x] Partially — explain: easy to remove as a checklist, but governance changes would need review if promoted into a release gate.

## Smallest safe experiment


Pilot the checklist on the next Dark_Mellow release fix before making it a MAP-wide gate.

## Decision needed

Who must approve this before it can be promoted?

- [ ] Task DRI — within current task scope
- [ ] Review DRI — requires review gate
- [ ] State Steward — changes shared state
- [ ] Project DRI — changes project direction
- [x] Human Owner — changes MAP-level rules or governance

## Recommendation

- [ ] Park — valid but not the right time
- [ ] Reject — not worth pursuing
- [x] Test — run the smallest safe experiment
- [ ] Promote to task — evidence is sufficient, ready for HPOM

## Lifecycle close-out (2026-07-02, TASK-078)

Promoted via PROMO-0005 into MAP_System/notes/release-path-checklist.md (TASK-078, pending peer review). Promoted as a checklist artifact only — the card's Human Owner boundary for gate-level governance is respected and stays open.
