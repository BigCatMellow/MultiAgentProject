# Context Routing Guide

Use this guide to decide which MAP files to read together.

MAP files are not independent thoughts. They work best as small linked memory
cells. Read the smallest useful set for the job, then follow references only
when the task needs more context.

## Default Context Stack

For most work, read:

1. `AGENTS.md` - rules of operation.
2. `shared/current-state.md` - live status and known issues.
3. `shared/memory-map.md` - where memory lives.
4. assigned task file in `tasks/`.
5. files listed in the task's `input_paths`.
6. files listed in the task's `output_paths` if they already exist.

Stop there unless something is unclear.

## File Relationships

```text
AGENTS.md
  -> shared/current-state.md
  -> shared/memory-map.md
  -> tasks/TASK-NNN.json
      -> input_paths
      -> output_paths
      -> artifacts/
      -> handoffs/

shared/current-state.md
  -> shared/improvement-backlog.md
  -> notes/operations-runbook.md
  -> notes/task-metadata-repair-plan.md

shared/memory-map.md
  -> shared/README.md
  -> notes/README.md
  -> folder README files

tasks/TASK-NNN.json
  -> workflow/task_graph.json
  -> events/events.jsonl
  -> artifacts/reviews/

handoffs/
  -> relevant task
  -> changed files
  -> verification records

inbox/
  -> notes/communication-guide.md
  -> owning agent or helper note
```

## Common Situations

### Starting A Task

Read:

- `AGENTS.md`
- `shared/current-state.md`
- `tasks/TASK-NNN.json`
- task `input_paths`
- `shared/decisions.md` if the task touches architecture, policy, or ownership

Then check:

- `workflow/task_graph.json` if dependencies or status are unclear
- `events/events.jsonl` for recent activity on the task

### Reviewing Work

Read:

- `notes/review-guide.md`
- task file
- task `acceptance_criteria`
- task `output_paths`
- relevant review template in `templates/review.md`

Then verify with:

- commands named by the task or artifact
- `notes/operations-runbook.md` for standard MAP commands

### Repairing Broken MAP State

Read:

- `shared/current-state.md`
- `shared/improvement-backlog.md`
- `notes/operations-runbook.md`
- relevant repair guide, such as `notes/task-metadata-repair-plan.md`

Then inspect:

- task files
- `workflow/task_graph.json`
- `events/events.jsonl`
- related handoffs or artifacts

### Making A Decision

Read:

- `shared/decisions.md`
- `shared/unresolved-questions.md`
- `shared/constraints.md`
- related task or artifact context
- `templates/decision.md`

Record approved durable decisions in `shared/decisions.md`. Keep open questions
in `shared/unresolved-questions.md`.

### Working With Helpers

Read:

- `notes/helper-agent-guide.md`
- `notes/communication-guide.md`
- relevant `inbox/helpers/*.md`
- owning task file

Record helper findings in `inbox/helpers/`. Move final decisions or task changes
to canonical files.

### Creating A New Project From MAP

Read:

- `notes/brain-organization-guide.md`
- `templates/`
- `shared/memory-map.md`
- folder README files

Copy the structure, but rewrite `shared/current-state.md`, `project-brief.md`,
`requirements.md`, and task files for the new project.

## When To Stop Reading

Stop adding context when:

- the next action is clear;
- the task's input and output paths are understood;
- current state and decisions do not conflict;
- you can verify the work with a command or concrete file check.

Do not keep reading historical artifacts just because they exist.

## When To Follow More Links

Follow more links when:

- a file says it is superseded;
- task intent is unclear;
- current state conflicts with an artifact;
- a validation command fails;
- ownership or approval status is ambiguous;
- a change affects architecture, policy, security, or data safety.

## Priority Order During Conflicts

When files disagree, prefer this order:

1. explicit user instruction;
2. `AGENTS.md`;
3. `shared/current-state.md`;
4. `shared/decisions.md`;
5. current task file and `workflow/task_graph.json`;
6. executable code and validation results;
7. recent handoffs;
8. historical artifacts.

If the conflict changes scope or ownership, record it in a handoff, event, or
unresolved question before continuing.
