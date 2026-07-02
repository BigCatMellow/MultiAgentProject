# Idea Card

Idea ID: IDEA-0010
Project: MAP
Source insight or synthesis: INS-0009
Owner: codex-lab-lema
Date: 2026-07-02
Status: CANDIDATE

## Idea


Add a proactive E/I operator-friction scouting loop for CommandCenterUI and lab workflows

## Problem or opportunity


Agents are still waiting for the operator to name obvious operator-workflow
affordances after the evidence is already visible in repeated CommandCenterUI
work. The E/I layer should notice those patterns, capture them, and propose
bounded improvements before the operator has to spell them out.

## Why now


TASK-086 through TASK-094 repeatedly improved the same operator-facing lab
surface. The operator explicitly identified quote/reply, attention inbox,
approval surface, and auto-mode ergonomics as examples of what E/I should
have surfaced proactively.

## Expected benefit


Reduces the operator's need to invent every UX/system improvement and makes E/I visibly useful while preserving HPOM gates.

## Cost


Small process cost: agents need a short E/I pass during task closeout or
review when operator-facing friction is observed.

## Reversibility

Can this be undone easily?

- [ ] Yes
- [ ] No
- [x] Partially — explain: A scouting loop can be stopped, but once it creates
      candidate records those records should be closed or superseded rather
      than deleted.

## Smallest safe experiment


For the next operator-facing CommandCenterUI task, require a short closeout
note: either "no new operator-friction candidate found" or one evidence-backed
insight/idea card. Do not promote automatically.

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
