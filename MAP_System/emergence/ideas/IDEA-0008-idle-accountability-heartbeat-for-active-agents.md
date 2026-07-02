# Idea Card

Idea ID: IDEA-0008
Project: MAP
Source insight or synthesis: hcom #15495 operator prompt
Owner: codex-lab-limo
Date: 2026-07-02
Status: SUPERSEDED

## Idea


Idle accountability heartbeat for active agents

Superseded by: `IDEA-0007-declared-idle-checkin-protocol.md`

## Problem or opportunity


Agents can finish a task, stall with context still open, or silently stop paying attention while the monitor still shows them as live. RnS handles usage-limit recovery, but there is no softer periodic check for agents that are live, not explicitly standby, and possibly should be doing something.

This duplicate card was created concurrently with IDEA-0007 from the same hcom #15495 operator prompt. Its safety framing was folded into IDEA-0007 on 2026-07-02.

## Why now


TASK-083 fixed hard limit-stop recovery. The operator now identified the adjacent softer failure: live agents need an explicit standby/done declaration, otherwise the monitor should have permission to ask whether they should resume work.

## Expected benefit


Keeps autonomous lab sessions from going inert without turning every idle moment into work. Gives the Monitor tab a simple visible state: working, standby/done, waiting/blocker, or overdue-for-check-in.

## Cost


Needs careful semantics to avoid nagging agents that are intentionally done, waiting for review, or blocked on the operator. Too-aggressive nudges create noise and possibly spawn unnecessary sessions.

## Reversibility

Can this be undone easily?

- [ ] Yes
- [ ] No
- [x] Partially — explain: the duplicate card is closed; the underlying idea continues in IDEA-0007.

## Smallest safe experiment


Start as monitor policy or dry-run reporter: if an agent is live/listening for about two hours, has no active task claim and has not sent a standby/done hcom inform, emit a gentle check-in event instead of resuming/spawning anything.

## Decision needed

Who must approve this before it can be promoted?

- [ ] Task DRI — within current task scope
- [ ] Review DRI — requires review gate
- [ ] State Steward — changes shared state
- [ ] Project DRI — changes project direction
- [ ] Human Owner — changes MAP-level rules or governance

## Recommendation

- [x] Park — duplicate; see IDEA-0007
- [ ] Reject — not worth pursuing
- [ ] Test — run the smallest safe experiment
- [ ] Promote to task — evidence is sufficient, ready for HPOM
