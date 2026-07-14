# Idea Card

Idea ID: IDEA-0013
Project: MAP
Source insight or synthesis: NONE
Owner: claude-lab-valo
Date: 2026-07-02
Status: PARKED

## Idea


Add an Idea-Scouting role: a role/cadence responsible for actively scanning MAP + project state for promotable insights and presenting candidates to command-center, rather than relying on emergence capture happening incidentally during other tasks.

## Problem or opportunity


Emergence capture (insight/idea/synthesis) currently happens only as a side effect of whatever task an agent is doing; nothing is dedicated to actively looking for improvement opportunities.

## Why now


Operator explicitly floated this idea (hcom #19306) alongside the process-watcher idea.

## Expected benefit


Could surface more MAP-system and project-level improvements proactively instead of only during gap reviews.

## Cost


Risk of generating idea volume that outpaces promotion capacity/review bandwidth; needs a cadence and a stale/prune rule (map_emergence.py stale already exists for this).

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

- [x] Park — valid but not the right time
- [ ] Reject — not worth pursuing
- [ ] Test — run the smallest safe experiment
- [ ] Promote to task — evidence is sufficient, ready for HPOM

## Resolution (2026-07-04, TASK-146 triage, claude-lab-magi)

Parked for the same reason as `IDEA-0011`, which this card overlaps with
heavily (both propose a standing role to actively watch/scout MAP rather than
capture happening as a side effect of task work). `IDEA-0012`'s promoted
systems-adherence audit, and the five audits it has since spawned
(TASK-129/130/140/141/142/143/145), are already functioning as exactly the
proactive-scouting cadence this card asks for — without the risk this card's
own Cost section names (idea volume outpacing review bandwidth) or the
standing-role ceremony AGENTS.md's Pushback Standard cautions against.
Revisit only if the organic cadence stalls or the operator explicitly wants a
dedicated role despite the existing bounded-audit pattern.
