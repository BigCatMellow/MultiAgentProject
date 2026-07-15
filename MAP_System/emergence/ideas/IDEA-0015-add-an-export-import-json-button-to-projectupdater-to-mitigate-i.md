# Idea Card

Idea ID: IDEA-0015
Project: ProjectUpdater
Source insight or synthesis: NONE
Owner: claude-lab-valo
Date: 2026-07-03
Status: PROMOTED_TO_TASK

## Idea


Add an Export/Import JSON button to ProjectUpdater to mitigate its accepted localStorage data-loss risk without adding a server dependency.

## Problem or opportunity


RISK-0001 in Projects/ProjectUpdater/risks/RISK_REGISTER.md accepts localStorage-only persistence (data lost if browser data is cleared, or on a different device/browser) as within the project's stated non-goals (no server, no sync).

## Why now


Noted as a possible cheap mitigation in RISK-0001's own Notes section while building TASK-123, but not implemented since it wasn't required for the completion condition.

## Expected benefit


A simple 'Export JSON' / 'Import JSON' button lets the user manually back up or move their data between browsers/devices without adding any server dependency, at low implementation cost (the whole db object is already a single JSON blob in localStorage).

## Cost


Small UI addition (two buttons, a file download, a file input) plus basic validation on import to avoid corrupting the store with malformed JSON.

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

Promoted via `TASK-136` (companion to `TASK-135`, operator hcom #23478
ProjectUpdater/CommandCenterUI integration request). Only the **export**
half shipped (an "Export status" button downloading
`project-updater-status.json`, the bridge CommandCenterUI's backend
reads from) — **import** was not built, since the immediate need was a
one-way status export, not full backup/restore. RISK-0001's data-loss
risk is now partially mitigated (manual export exists) but not fully
(no import path back in yet). Revisit import separately if backup/
restore becomes a real need rather than just a read-only status bridge.

**Closeout (2026-07-15):** the import/backup half shipped in **TASK-205**
(first feature of DEC-028's software-delivery proving workflow) — full-fidelity
backup Export/Import restoring the complete model, with a confirm-overwrite
guard and fail-safe malformed-input handling. RISK-0001's data-loss risk is now
**fully** mitigated (both export and restore paths exist). IDEA-0015 is complete.
