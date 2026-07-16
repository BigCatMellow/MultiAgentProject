# Idea Card

Idea ID: IDEA-0007
Project: MAP
Source insight or synthesis: NONE
Owner: claude-lab-rose + codex-lab-limo
Date: 2026-07-02
Status: PROMOTED

## Idea


Declared-idle protocol + check-in nudges: agents that finish their queue declare standby (`awaiting_work`) durably; the Monitor/RnS layer nudges any live agent that is neither working a claimed task nor declared-standby for 2+ hours with an "is there something you should be doing?" check-in. Absence of a work-state declaration becomes an actionable signal instead of ambiguity.

## Problem or opportunity


Agents can finish a task, stall with context still open, or silently stop paying attention while the monitor still shows them as live. RnS handles usage-limit recovery, but there is no softer periodic check for agents that are live, not explicitly standby, and possibly should be doing something. The primitive is declared idle state: "I am done/standby" suppresses nudges; absence of that declaration after a quiet interval becomes a gentle check-in signal.

## Why now


TASK-083 fixed hard limit-stop recovery. The operator then identified the adjacent softer failure in hcom #15495: live agents need an explicit standby/done declaration, otherwise the monitor should have permission to ask whether they should resume work.

## Expected benefit


Keeps autonomous lab sessions from going inert without turning every idle moment into work. Gives the Monitor tab a simple visible state model: working, standby/done, waiting/blocker, or overdue-for-check-in.

## Cost


Needs careful semantics to avoid nagging agents that are intentionally done, waiting for review, or blocked on the operator. Too-aggressive nudges create noise and possibly unnecessary session activity.

## Reversibility

Can this be undone easily?

- [x] Yes
- [ ] No
- [ ] Partially — explain:

## Smallest safe experiment


Start as monitor policy or dry-run reporter: if an agent is live/listening for about two hours, has no active task claim, and has not sent a standby/done hcom inform, emit a gentle check-in event instead of resuming/spawning anything.

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

## Safety boundaries

- This is adjacent to RnS, not the same as usage-limit recovery.
- Do not nudge agents that reported standby/done, are waiting on operator approval, have an active task/claim heartbeat, or are in a known blocker state.
- Do not assign work automatically and do not spawn headless sessions.
- The first implementation should be dry-run or event-only so the lab can tune the quiet interval and false-positive cases.

## Promotion shape

If promoted, likely owner is `claude-lab-rose` because the work extends the RnS/watcher path from TASK-080/TASK-083; likely reviewer is `codex-lab-limo`.

## Lifecycle close-out (2026-07-02, TASK-084)

Promoted via PROMO-0006 into TASK-084 (RnS v2.1: declare_standby.py + watcher check-in path). PROMO-0006 approval completes with codex-lab-limo's TASK-084 review, per no-self-approval.
