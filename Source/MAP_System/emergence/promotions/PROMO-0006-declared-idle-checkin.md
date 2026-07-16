# Promotion Record

Promotion ID: PROMO-0006
Project: MAP
Source idea: IDEA-0007
Source experiment: NONE
Decision owner: claude-lab-rose
Date: 2026-07-02
Status: APPROVED

## What is being promoted?


Promote the declared-idle/check-in protocol into a watcher extension (RnS v2.1): declare_standby helper + 2h check-in nudges for live agents with no claim and no declaration, honoring the card's safety boundaries (no nudges to declared/claimed/blocked agents, no auto-assignment, no headless spawns).

## Why it should become real work


Human Owner requested the behavior directly (hcom #15495) -- the card's Human-Owner approval box is satisfied by the request itself. All inputs (hcom snapshot, SQLite claims, status.json) already flow through the watcher.

## What it becomes

Choose one:

- [ ] HPOM task — requires implementation work
- [ ] Decision record — resolves a design or architecture question
- [ ] Shared-state update — corrects or extends a current-state or requirements file
- [ ] Project artifact — produces a document, template, or reference
- [x] MAP system improvement — improves MAP's own process or tooling
- [ ] Parked reference — valid but not the right time; record and stop

## Required next action

Done in TASK-084: watcher check-in path + declare_standby.py helper + docs + tests. Peer review of TASK-084 is the approval step.

## Approval

Approved by: codex-lab-limo via TASK-084 peer review. Human Owner behavior-request on record (hcom #15495).
Date: 2026-07-02

---

*A promotion record without a completed Approval field is PROPOSED, not APPROVED.*
*Self-approval is not allowed for substantive MAP-level changes.*
