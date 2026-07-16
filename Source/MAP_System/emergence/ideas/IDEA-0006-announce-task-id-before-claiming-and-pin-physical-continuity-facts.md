# Idea Card

Idea ID: IDEA-0006
Project: MAP
Source insight or synthesis: INS-0006
Owner: command-center
Date: 2026-07-01
Status: PROMOTED_TO_TASK

## Idea

Two small process fixes, bundled because they surfaced in the same session
and are both about parallel agents editing shared state without a shared
source of truth:

1. Require an hcom `inform` announcing a new task ID before writing the task
   file, so a same-window collision gets caught before either agent commits,
   not after.
2. When multiple agents add descriptive/sensory prose to the same scene in
   separate passes, a fast-moving physical fact (is the vehicle moving or
   stopped, is a door open or closed, who is holding what) is the most likely
   thing to silently contradict between passes, because each agent is reading
   the scene fresh rather than tracking state across edits.

## Problem or opportunity

INS-0006 documents a real near-miss (task ID collision, an accidental `rm` of
another agent's approved file, caught and fixed) and a real caught error (a
car described as "already in park" three lines after "the car kept moving,"
introduced during a parallel Ch10 expansion pass and caught only because a
reviewer happened to read closely). Both happened in the same session, both
are symptoms of the same root cause: parallel low-supervision agent work
needs a cheap coordination signal, and right now the only one in use is
"hope the other agent notices."

## Why now

Command-center has been explicit this session about wanting less
hand-holding and more actual parallel use of the MAP system's agents and
helpers. That's the right direction, but it raises the collision rate for
exactly these two failure modes. Better to name the fix now, while the
concrete examples are fresh, than to wait for a collision that isn't caught.

## Expected benefit

- Fewer silent task-file collisions as agents create more tasks with less
  operator involvement.
- Fewer physical-continuity errors slipping through automated review (the
  `chapter_review_scan.py` scanner checks prose patterns, not cross-scene
  physical state, so this class of error is currently only caught by a human
  or agent doing a close read).

## Cost

Low. Fix 1 is a one-line process convention, no tooling change required.
Fix 2 could stay a process convention too (a reviewer checklist item: "does
any added sentence assert a physical state — position, motion, possession —
that contradicts a nearby line?"), or be added as a lightweight check to
`chapter_review_scan.py` if this recurs.

## Reversibility

- [x] Yes — both are process conventions, not code or schema changes.

## Smallest safe experiment

Add both as explicit checklist items the next time two agents run a parallel
expansion or review pass — no tooling build required to test whether they
reduce recurrence.

## Decision needed

- [ ] Task DRI — within current task scope
- [ ] Review DRI — requires review gate
- [ ] State Steward — changes shared state
- [ ] Project DRI — changes project direction
- [ ] Human Owner — changes MAP-level rules or governance

Neither fix requires human-owner-level sign-off — both are conventions core
agents can adopt directly. Recorded here so they're visible and reusable
rather than living only in this session's hcom transcript.

## Recommendation

- [ ] Park — valid but not the right time
- [ ] Reject — not worth pursuing
- [x] Test — run the smallest safe experiment
- [ ] Promote to task — evidence is sufficient, ready for HPOM

## Lifecycle close-out (2026-07-02, TASK-075)

Fix 1 (atomic/announced task IDs) is being implemented by TASK-065. Fix 2 (physical-continuity check in parallel prose passes) was adopted as a working convention during TASK-024 and is documented in the TASK-063/064 audit trail. Closed during TASK-075.
