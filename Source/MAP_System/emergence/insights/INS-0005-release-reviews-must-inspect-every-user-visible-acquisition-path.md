# Insight Record

Insight ID: INS-0005
Project: MAP
Related task: TASK-059
Detected by: codex-lab-maki
Date: 2026-07-01
Status: PROMOTED

## Short description


Release reviews must inspect every user-visible acquisition path, not just the source tree.

## Trigger


Dark_Mellow wallpaper issue persisted after source installer fix because a stale dated ZIP remained visible in the GitHub package.

## The synthesis


For user-facing packages, the effective product is the combination of source tree, generated downloads, retained archives, launcher files, and README instructions.

## Why it might matter


Users naturally click visible ZIP files and legacy docs; if those artifacts are stale, the current code can be correct while the delivered experience remains broken.

## Evidence


The retained Mellow-Dark-theme-2026-06-30.zip contains the old installer with no wallpaper install path, while README.md keeps the dated ZIP visible as retained upload material.

## Risk


Without a release-path checklist, MAP tasks can mark a fix complete while an alternate user path still ships the old behavior.

## Scope


Only the files and artifacts named in this record.

## Recommended next action

Choose one:

- [ ] Ignore — not worth preserving
- [ ] Park for later — valid but low priority
- [ ] Create follow-up task — actionable now
- [x] Create idea card — needs more development
- [ ] Run small experiment — testable now
- [ ] Escalate to Human Owner / Project DRI — requires decision authority

## Notes

- Converted into `IDEA-0005` during TASK-059.

## Lifecycle close-out (2026-07-02, TASK-078)

Promoted via IDEA-0005 / PROMO-0005 into MAP_System/notes/release-path-checklist.md (TASK-078, pending peer review). Gate status remains a Human Owner decision.
