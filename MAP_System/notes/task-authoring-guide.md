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

Historical tasks may have incomplete output paths. Do not copy that pattern.

## Repair Pattern

When repairing incomplete task metadata, preserve original task intent instead
of inventing new scope.
