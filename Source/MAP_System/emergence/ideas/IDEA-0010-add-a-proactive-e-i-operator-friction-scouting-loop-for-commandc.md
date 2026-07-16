# Idea Card

Idea ID: IDEA-0010
Project: MAP
Source insight or synthesis: INS-0009
Owner: codex-lab-lema
Date: 2026-07-02
Status: PROMOTED_TO_TASK

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
- [ ] Test — run the smallest safe experiment
- [x] Promote to task — evidence is sufficient, ready for HPOM

## Resolution (2026-07-04, TASK-146 triage, claude-lab-magi)

Promoted, scoped down from a "scouting loop" to exactly the card's own
smallest-safe-experiment: a closeout habit, not a new role or mandatory gate
(see `IDEA-0011`/`IDEA-0013` resolutions for why a standing role was parked
instead). This card named Human Owner approval as required since it touches
MAP-level habit; treating the operator's 2026-07-04 full-MAP-renewal request
(hcom #25059), which explicitly named "keep an eye on E/I and see what we
can come up with to improve things" and "don't be afraid to add new rules
and procedures... I trust you," as that approval for a small, reversible,
non-mandatory habit addition. Implemented as a new "Operator-Facing Friction
Closeout Habit" section in `notes/task-authoring-guide.md`. Not wired into
`release_task.py` as a hard gate (unlike DEC-026's emergence-capture line):
unlike Emergence capture, which applies to every task, this only applies to
operator-facing-surface tasks, which cannot be mechanically detected from a
task record alone — forcing the checkbox onto irrelevant tasks would be the
same box-ticking-ceremony risk DEC-026 already named. Revisit as a mechanical
gate only if the habit proves not to stick on its own.
