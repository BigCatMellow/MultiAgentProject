<!-- hpom: file: shared/memory-map.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: HPOM sprint review 2026-06-29 -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Memory Map

This file is the index for MAP's durable Markdown memory.

Use it to avoid treating every Markdown file as equally current. Some files are
canonical operating memory; others are historical artifacts from completed work.

## Read First

For a normal agent session, read in this order:

1. `AGENTS.md`
2. `shared/current-state.md`
3. `shared/memory-map.md`
4. the assigned task file in `tasks/`
5. only the input paths and artifacts named by that task

Do not load the entire Markdown tree by default. MAP works best when agents read
the live memory first and then pull scoped context as needed.

## Canonical Operating Memory

- `AGENTS.md` - required operating rules for all agents.
- `README.md` - system overview and current health note.
- `shared/current-state.md` - live status, known issues, and active risks.
- `shared/architecture.md` - concise current architecture overview.
- `shared/project-brief.md` - objective and completion condition.
- `shared/requirements.md` - requirements and current capabilities.
- `shared/constraints.md` - hard boundaries and safety constraints.
- `shared/decisions.md` - approved architecture and coordination decisions.
- `shared/unresolved-questions.md` - open questions that still need decisions.
- `shared/improvement-backlog.md` - known improvements that need intentional follow-up.
- `shared/glossary.md` - shared vocabulary.

## Operating Runbooks

- `notes/operations-runbook.md` - commands for status, tests, validation, and recovery.
- `notes/task-authoring-guide.md` - how to create and repair task records.
- `notes/task-metadata-repair-plan.md` - focused plan for repairing current task metadata gaps.
- `notes/state-machine-guardrails.md` - READY gate and task-state transition guardrails.
- `notes/architect-agent-guide.md` - Architect/Shaper role for turning ideas into claimable tasks.
- `notes/review-guide.md` - review verdicts, severities, and artifact format.
- `notes/helper-agent-guide.md` - helper-agent setup, notes, and stop conditions.
- `notes/local-model-helper-guide.md` - local Ollama/Aider helper policy and boundaries.
- `notes/communication-guide.md` - routing rules for core agents, helpers, inbox notes, and handoffs.
- `notes/communication-architecture.md` - thread IDs, message IDs, promotion rules, and cross-references.
- `notes/documentation-style-guide.md` - structured writing rules for all MAP files.
- `notes/context-routing-guide.md` - which MAP files to read together for common situations.
- `notes/brain-compaction-guide.md` - how to keep active memory lean while preserving history.
- `notes/brain-organization-guide.md` - reusable guide for organizing new project brains.
- `notes/command-center-later.md` - deferred hardening items for the next command-center session.
- `notes/git-setup.md` - local Git wrapper details.
- `notes/how-to-work-with-codex-and-claude.md` - collaboration loop.

## Runtime And Workflow Context

- `graph/README.md` - LangGraph runner behavior and command examples.
- `graph/dependency-notes.md` - graph dependency notes.
- `workflow/templates/state_snapshot.yaml` - structured resume handoff format.
- `templates/` - reusable templates for tasks, handoffs, reviews, decisions, events, and current-state docs.

## Historical Memory

- `artifacts/reviews/` - review records. Useful for provenance, but not always current.
- `artifacts/tests/` - test notes. Useful for verification history, but commands may reference older paths.
- `artifacts/planning/` - design notes that may be superseded by implementation.
- `handoffs/` - session handoffs and snapshots. Read relevant recent ones only.
- `inbox/` - agent-to-agent notes. Treat as scoped context, not global truth.
- `archive/` - compacted historical memory. Read only when a current file points there.

When historical memory conflicts with canonical operating memory, prefer
`shared/`, `AGENTS.md`, current task files, and executable scripts.
