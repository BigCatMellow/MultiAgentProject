# Idea Card

Idea ID: IDEA-0004
Project: MAP
Source insight or synthesis: CommandCenterUI TASK-056 deep review at operator request
Owner: claude-lab-taro
Date: 2026-07-01
Status: PROMOTED

## Idea


Require a second, security-focused review pass for any task that adds a network-facing or write-capable component

## Problem or opportunity


My first-pass review of app/server.py (TASK-056) approved a working, input-validated backend but missed a real CSRF/drive-by gap on POST /api/hcom/send - any other page open in the same browser could silently trigger an hcom send once the app ran in send-enabled mode. A second, explicitly security-framed pass (prompted only because the operator asked for a deeper look) caught it.

## Why now


CommandCenterUI is the first MAP-built component with a live local server and a real write endpoint into the multi-agent bus; more of these are likely as the lab UI work continues, so the gap in review depth is reproducible, not a one-off.

## Expected benefit


Catches trust-boundary issues (auth, CSRF, injection, path traversal) that a functional/scope-focused review pass tends to miss, without requiring every review to be security-depth by default.

## Cost


One extra review pass (time only) specifically for tasks whose output_paths or description indicate a new server/listener/endpoint/write-capable integration; skip for purely static or read-only work.

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
- [ ] Promote to task — evidence is sufficient, ready for HPOM

## Lifecycle close-out (2026-07-02, TASK-078)

Promoted via PROMO-0004 into MAP_System/AGENTS.md Review Standard: 'Security Second Pass' (TASK-078, pending peer review).
