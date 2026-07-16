# Local Model Helper Guide

## Status

- Policy status: `available`
- Source brief: this file (canonical — Guidelines copy removed)
- Runtime status: `helper-capability-only`
- Core-agent status: `not-registered`
- Owner: `command-center`

## Rule

- Paid/core agents hold authority, judgment, and final responsibility.
- Local assistants reduce paid-model load through scoped support work.
- Use local models for low-risk support work.
- Do not use local models as final authority.
- Do not run assistants in an unreachable background mode; the operator must be
  able to inspect and interact through a visible terminal or the AI Command
  Center.
- Do not register local models as core agents until health checks and manual
  workflows are proven.
- Aider is a tool/workbench, not a model.

## Operating Pattern

```text
core agent owns task
local assistant performs scoped draft/check/summary
core agent reviews local output
core agent applies or rejects output
separate reviewer validates final work when required
```

## Output Shape

Preferred local-assistant outputs:

- `summary`
- `classification`
- `checklist-result`
- `draft`
- `recommendation`
- `diff-suggestion`

Denied local-assistant outputs:

- `final-decision`
- `approved-review`
- `task-completion-claim`
- `unbounded-rewrite`
- `architecture-change`

## Capability Map

| Helper | Type | Default Use | Authority |
|---|---|---|---|
| `llama3.2:3b` | model | project-brain summary, orientation, event digest | draft-only |
| `llama3.2:1b` | model | tiny summary, classification, routing hint | draft-only |
| `qwen2.5-coder:3b` | model | JSON, schemas, validators, SQLite helper logic | draft-only |
| `qwen2.5-coder:1.5b` | model | fast syntax/key/path checks | draft-only |
| `gemma3:4b` | model | acceptance criteria, markdown cleanup, review drafts | draft-only |
| `Aider` | tool | narrow supervised file edits with `qwen2.5-coder:3b` | edit-helper |

## Allowed Work

- Summarize `shared/current-state.md`.
- Digest recent `events/events.jsonl`.
- Classify raw input as `task`, `decision`, `event`, `review`, or `question`.
- Check task JSON against `templates/task.json`.
- Draft binary acceptance criteria for review.
- Clean markdown without meaning changes.
- Suggest validator/script edits.
- Prepare review packets for paid/core agents.
- Produce recommendations for a core agent to accept, revise, or reject.

## Denied Work

- Final architecture decision.
- Final review approval.
- Security-sensitive change.
- Broad refactor.
- Broad file rewrite.
- Ambiguous user-intent decision.
- Unsupervised project-wide run.
- Hidden recommendation source.

## Recording Requirement

When local helper output affects MAP work, record:

- helper model/tool;
- owning core agent;
- task id or reason;
- input paths;
- output path or recommendation path;
- review owner.

## Aider Guardrail

Before Aider:

- normal root Git is available;
- current work has a clean baseline commit when the edit is more than narrow;
- task has explicit `output_paths`;
- target files are named;
- forbidden files are named when relevant;
- `map-git status` or Git state is known;
- prompt is scoped to one narrow edit;
- review is assigned to a different authority.

Denied Aider prompts:

- `improve MAP`
- `clean up the system`
- `fix whatever you find`
- `rewrite the docs`
- `make the agents smarter`

## Helper Names

- `local-map-summarizer`
- `local-json-checker`
- `local-validator-helper`
- `local-markdown-cleanup`
- `local-aider-worker`

## Pushback Triggers

- local helper would replace final review;
- local helper would edit broad file sets;
- local helper would decide architecture;
- local helper would infer missing user intent;
- local helper would run without scoped task;
- local helper source would not be recorded.

## Later

- Add command-center launch wrappers after manual workflow proves useful.
- Add `ollama list` health check.
- Add Aider availability check.
- Add helper registration only after checks exist.
