# Brain Compaction Guide

MAP's active brain should stay lean. Completed work should remain traceable, but
old narrative should not accumulate forever in `shared/current-state.md`,
`shared/decisions.md`, or other high-priority files.

## Goal

Turn detailed historical activity into compact structural memory.

Good compaction:

- preserves decisions, risks, and final outcomes;
- removes repetitive progress narrative from active files;
- points to archived raw detail;
- keeps future agents from rereading stale context;
- does not destroy audit history.

## Active Memory Budget

Treat these files as active memory and keep them concise:

- `shared/current-state.md`
- `shared/memory-map.md`
- `shared/requirements.md`
- `shared/decisions.md`
- `shared/unresolved-questions.md`
- `shared/improvement-backlog.md`
- folder `README.md` files

If a file starts becoming a transcript, compact it.

## Compaction Triggers

Run a compaction pass when any of these happen:

- 10 tasks have been completed or approved since the last compaction;
- `events/events.jsonl` becomes hard to scan;
- `shared/current-state.md` has more than a few stale completed-work notes;
- decisions contain long narrative instead of concise decision records;
- a project phase ends;
- an agent reports confusion from conflicting historical context.

## Compaction Inputs

Read only the relevant range:

- recent `events/events.jsonl` entries;
- completed task files;
- recent handoffs;
- recent review artifacts;
- new or changed decisions;
- current known issues and unresolved questions.

Do not read all historical artifacts unless the compaction scope requires it.

## Compaction Outputs

Create a summary in:

```text
archive/compactions/
```

Recommended filename:

```text
compaction-YYYY-MM-DD-tasks-NNN-NNN.md
```

Then update active memory:

- `shared/current-state.md` - only current capabilities, risks, and next maintenance.
- `shared/decisions.md` - concise approved decisions, not long debate.
- `shared/unresolved-questions.md` - only still-open questions.
- `shared/improvement-backlog.md` - only still-actionable follow-ups.
- `shared/memory-map.md` - link to the latest compaction if useful.

## What To Archive

Move or summarize away:

- verbose completed-task progress notes;
- superseded status descriptions;
- old helper chatter after findings are integrated;
- stale review details after verdict and final finding summary are captured;
- repeated event narrative that has a clear final outcome.

Keep active:

- current known health issues;
- active agent assumptions;
- approved decisions that still govern behavior;
- unresolved questions;
- next recommended actions;
- paths to canonical outputs.

## Compaction Summary Shape

Use `templates/compaction-summary.md`.

Use structured fields and terse bullets. Avoid paragraph narrative unless a
tradeoff or anomaly needs explanation.

Every compaction summary should include:

- scope;
- source files;
- tasks covered;
- durable outcomes;
- decisions preserved;
- questions closed;
- open follow-ups;
- archive links;
- active files updated.

Compaction summaries should follow `notes/communication-architecture.md`:

- stable thread ID when the compaction came from an agent exchange;
- task IDs for covered work;
- source paths for raw history;
- outcome locations for active-memory updates;
- explicit open follow-ups.

## Safety Rules

- Do not delete raw logs during compaction.
- Do not rewrite history to make old work look cleaner.
- Do not remove an active decision unless it is explicitly superseded.
- Do not close unresolved questions without evidence.
- Leave backlinks from active files to archive summaries when useful.
- Prefer structured bullets over full prose so agents can scan the summary.

## Suggested Helper Role

A helper can perform compaction if its scope is explicit:

```text
helper-memory-compactor
```

The helper should not make new product decisions. Its job is to summarize,
classify, archive, and propose active-memory edits for review by a core agent.
