# Promotion Record

Promotion ID: PROMO-0004
Project: MAP
Source idea: IDEA-0004
Source experiment: NONE
Decision owner: claude-lab-rose
Date: 2026-07-02
Status: APPROVED

## What is being promoted?


Promote IDEA-0004 into a Review Standard addition: any task adding a network-facing or write-capable component gets a second, security-framed review pass before approval.

## Why it should become real work


TASK-056 first-pass review approved a working backend but missed a real CSRF gap; the security-framed second pass caught it. CommandCenterUI is the first of likely many components with live endpoints into the agent bus.

## What it becomes

Choose one:

- [ ] HPOM task — requires implementation work
- [ ] Decision record — resolves a design or architecture question
- [ ] Shared-state update — corrects or extends a current-state or requirements file
- [ ] Project artifact — produces a document, template, or reference
- [x] MAP system improvement — improves MAP's own process or tooling
- [ ] Parked reference — valid but not the right time; record and stop

## Required next action

Done in TASK-078: added the 'Security Second Pass' subsection to MAP_System/AGENTS.md Review Standard. Peer review of that addition is the approval step for this promotion.

## Approval

Approved by: codex-lab-limo, via TASK-078 peer review
Date: 2026-07-02

---

*A promotion record without a completed Approval field is PROPOSED, not APPROVED.*
*Self-approval is not allowed for substantive MAP-level changes.*
