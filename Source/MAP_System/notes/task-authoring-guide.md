# Task Authoring Guide

Every task should be useful to a future agent that has no chat context.

## Required Fields

- `task_id` - stable ID such as `TASK-048`.
- `title` - short action-oriented title.
- `task_type` - implementation, review, architecture, planning, research, or maintenance.
- `role` - expected worker role.
- `status` - READY, IN_PROGRESS, SUBMITTED, CHANGES_REQUESTED, DONE, APPROVED, or BLOCKED.
- `dependencies` - task IDs that must finish first.
- `owner` - accountable agent, or empty only before assignment.
- `description` - enough context to execute the task without chat history.
- `input_paths` - files the worker should read.
- `output_paths` - files the task owns or creates.
- `acceptance_criteria` - concrete checks that define done.

## Acceptance Criteria

Good criteria are observable:

- names the expected file, command, behavior, or artifact;
- can be verified by a reviewer;
- avoids vague wording such as "improve quality" without a measurable target;
- includes failure or edge-case behavior when relevant.

## Output Paths

Output paths are ownership boundaries. If a task needs to edit outside its
listed paths, create a handoff or update the task before continuing.

Any file touched by an Edit or Write call counts as an output path — this
includes a one-line cross-link backlink added to another system's
document, not just the task's named primary deliverables. Register it in
`output_paths` before submission, not after a reviewer flags it (see
RETRO-0001 in `RETROSPECTIVE_SYSTEM.md`).

Historical tasks may have incomplete output paths. Do not copy that pattern.

## Repair Pattern

When repairing incomplete task metadata, preserve original task intent instead
of inventing new scope.

## Operator-Facing Friction Closeout Habit

For any task that touches an operator-facing surface (CommandCenterUI, the
Monitor tab, a lab workflow the operator directly interacts with), add one
line to the closeout summary (event log entry, handoff, or release-checklist
Summary section) before submitting: either

- "no new operator-friction candidate found", or
- a link to one evidence-backed Emergence insight/idea card capturing a
  friction point noticed during the work.

This does not require a new role or a mandatory release gate (see
`IDEA-0011`/`IDEA-0013`'s resolution notes for why a standing scouting role
was parked instead). It is a habit, not a mechanical check: the point is
that repeated operator-facing work (TASK-086 through TASK-094 hit the same
CommandCenterUI friction more than once before anyone captured it as an
idea) should surface improvement candidates without the operator having to
name every one first. `map_emergence.py stale` already exists to prevent
candidates from piling up unreviewed.

Origin: `IDEA-0010` (promoted 2026-07-04, TASK-146), operator-approved as
part of the 2026-07-04 full-MAP-renewal request (hcom #25059) naming E/I
improvement as an explicit goal.
