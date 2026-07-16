# Brain Organization Guide

Use this guide when creating a new MAP-style project. The goal is to give AI
agents a durable project brain that is easy to read, update, and trust.

See `MAP_System/PROJECT_BOOTSTRAPPING_SYSTEM.md` and
`MAP_System/NEW_PROJECT_WIZARD.md` for the bootstrap workflow that uses
this layout — what a new project must establish (intent, assumptions,
research needs, quality standards, risks, decision paths) before its
first task, and the step-by-step checklist for doing so.

## Core Principle

Separate live truth from history.

Agents should be able to answer these questions quickly:

- What is true now?
- What work is next?
- What rules must I follow?
- What context is historical only?
- Where do I record progress?
- Where do I hand work to another agent?

If every Markdown file looks equally important, agents waste context and make
bad assumptions.

## Recommended Brain Layout

```text
PROJECT/
  AGENTS.md
  README.md
  shared/
    README.md
    current-state.md
    memory-map.md
    project-brief.md
    requirements.md
    constraints.md
    decisions.md
    unresolved-questions.md
    glossary.md
  tasks/
    README.md
    TASK-001.json
  workflow/
    README.md
    task_graph.json
    runtime_policy.yaml
    approval_rules.yaml
  notes/
    README.md
    operations-runbook.md
    task-authoring-guide.md
    review-guide.md
    helper-agent-guide.md
    communication-guide.md
    documentation-style-guide.md
    context-routing-guide.md
    brain-compaction-guide.md
  templates/
    README.md
    task.json
    handoff.md
    review.md
    decision.md
    current-state.md
    event.jsonl
  artifacts/
    README.md
    planning/
    reviews/
    tests/
    research/
    drafts/
    final/
  handoffs/
    README.md
  inbox/
    README.md
    helpers/
  events/
    README.md
    events.jsonl
  archive/
    README.md
    compactions/
```

## Folder Roles

### `shared/`

The live brain. Files here should be trustworthy current truth.

Use for:

- project objective;
- current status;
- requirements;
- constraints;
- approved decisions;
- unresolved questions;
- vocabulary.

Do not use for:

- test transcripts;
- one-off reviews;
- task-specific drafts;
- historical notes that may become stale.

### `tasks/`

The executable work queue.

Each task should be understandable without chat history and should include:

- owner or intended role;
- input paths;
- output paths;
- dependencies;
- acceptance criteria;
- status.

Tasks are not scratch notes. If a task is vague, agents will either stall or
invent intent.

### `workflow/`

Machine-readable routing and policy.

Use for:

- task graph;
- runtime policy;
- approval rules;
- workflow templates.

Human explanations can live in `workflow/README.md`, but core project truth
belongs in `shared/`.

### `notes/`

Runbooks and reusable guidance.

Use for:

- operations commands;
- task authoring rules;
- Git or environment setup;
- collaboration procedures.

Notes can explain how to do something. They should not quietly override
`shared/decisions.md`.

### `artifacts/`

Historical work products and evidence.

Use for:

- planning docs;
- reviews;
- test notes;
- research;
- final deliverables.

Artifacts may become stale. Agents should read them when a current task points
to them, not as default global memory.

### `handoffs/`

Continuity between agents or sessions.

Use for:

- work that another agent should review;
- work that another agent should continue;
- state snapshots before a session ends;
- summaries of partially completed work.

Handoffs should point to files instead of copying large context.

### `inbox/`

Scoped agent-to-agent notes.

Use for:

- notes intended for one agent;
- helper-agent findings;
- temporary coordination that is more durable than chat.

If the note changes project truth, move the result into `shared/decisions.md`,
`shared/current-state.md`, or a task file.

### `events/`

Append-only activity log.

Use for compact records:

- progress;
- submissions;
- approvals;
- questions;
- answers;
- handoff notices;
- decisions recorded.

Events are breadcrumbs, not full documentation.

## Required Index Files

Every major folder should have a `README.md` that says:

- what belongs here;
- what does not belong here;
- how agents should use it;
- which files are canonical.

Every project should also have:

- `shared/memory-map.md` - map of the project brain;
- `shared/current-state.md` - live operational status;
- `notes/operations-runbook.md` - commands and recovery steps;
- `notes/task-authoring-guide.md` - task quality rules.
- `templates/` - reusable starting points for common project records.
- `notes/brain-compaction-guide.md` - maintenance routine for keeping active memory lean.
- `notes/documentation-style-guide.md` - structured writing rules for all memory files.

## Read Order For Agents

Default read order:

1. `AGENTS.md`
2. `shared/current-state.md`
3. `shared/memory-map.md`
4. the assigned task file
5. relevant `shared/` files named by the task
6. task input paths
7. relevant artifacts or handoffs named by the task

Do not read the whole Markdown tree unless the task is explicitly an audit.

## Naming Rules

Use lowercase kebab-case for normal Markdown files:

```text
current-state.md
task-authoring-guide.md
operations-runbook.md
```

Keep standard entrypoints as conventional names:

```text
AGENTS.md
README.md
CLAUDE.md
```

Use stable structured names for task files:

```text
TASK-001.json
TASK-002.json
```

## What Makes A Good Brain Cell

A useful Markdown file is:

- short enough to scan;
- clearly scoped;
- current or clearly marked historical;
- linked from an index;
- written for a future agent with no chat context;
- explicit about what should happen next.

A poor brain cell is:

- a dumping ground;
- full of stale commands;
- unclear about whether it is current;
- missing ownership or date context;
- disconnected from tasks and decisions.

## Maintenance Rules

When project reality changes:

1. Update `shared/current-state.md`.
2. Record durable decisions in `shared/decisions.md`.
3. Move open questions to `shared/unresolved-questions.md`.
4. Update task files and `workflow/task_graph.json` together.
5. Add handoffs when another agent needs continuity.
6. Leave historical artifacts alone unless they are misleading in a live path.
7. Compact old narrative into `archive/` when active memory becomes noisy.

## Health Checks

Run these periodically:

- Do all major folders have README files?
- Does `shared/current-state.md` match the runnable system?
- Does `shared/memory-map.md` identify live vs historical memory?
- Do tasks have output paths and acceptance criteria?
- Do old artifacts reference paths that no longer exist?
- Can an agent find the next action in under five minutes?

If the answer is no, improve the brain before adding more work.
