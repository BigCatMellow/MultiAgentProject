# MultiAgentProject

This workspace is set up for collaboration between Codex, Claude Code, and a future LangGraph runtime.

The first working rule is simple: agents coordinate through durable files, task records, inbox notes, handoffs, and review artifacts instead of relying on one long shared chat.

All paths below are relative to `MAP_System/` unless stated otherwise.

## Start Here

1. Read `AGENTS.md`.
2. Read `shared/memory-map.md`.
3. Read `shared/project-brief.md`.
4. Pick or receive a task from `tasks/`.
5. Record progress in `events/events.jsonl` and agent-specific inbox/handoff files when needed.
6. Submit finished work as an artifact and request independent review.

## Important Paths

- `AGENTS.md` - shared operating rules for all agents.
- `CLAUDE.md` - Claude Code entrypoint; points back to the shared rules.
- `shared/` - project truth, decisions, requirements, and unresolved questions.
- `shared/architecture.md` - concise current architecture overview.
- `shared/current-state.md` - live operating status and known issues.
- `shared/memory-map.md` - guide to which Markdown files are canonical.
- `emergence/` - creative discovery layer for insights, synthesis notes, ideas, experiments, and promotion records before work enters HPOM.
- `workflow/` - task graph, runtime policy, approval rules, and LangGraph notes.
- `tasks/` - one JSON file per task.
- `artifacts/` - durable work products.
- `inbox/` - direct agent-to-agent notes.
- `handoffs/` - structured handoff packets.
- `graph/` - starter orchestration code and notes.
- `notes/operations-runbook.md` - common status, test, and recovery commands.
- `notes/task-authoring-guide.md` - task record quality rules.
- `notes/state-machine-guardrails.md` - READY gate and task-state transition guardrails.
- `notes/architect-agent-guide.md` - Architect/Shaper role for preparing claimable tasks.
- `notes/review-guide.md` - review verdicts, severity levels, and output format.
- `notes/helper-agent-guide.md` - temporary helper-agent setup and cleanup.
- `notes/communication-guide.md` - direct vs routed communication rules.
- `notes/communication-architecture.md` - traceable thread and message cross-reference model.
- `notes/documentation-style-guide.md` - structured writing rules for all MAP files.
- `notes/context-routing-guide.md` - how MAP files cross-reference and support each other.
- `notes/brain-compaction-guide.md` - how to archive old narrative and keep active memory lean.
- `notes/command-center-later.md` - deferred hardening items for the next command-center session.
- `templates/` - reusable task, review, handoff, decision, and status templates.
- `scripts/validate_task_graph.py` - mechanical task graph validator.
- `scripts/map-git` - compatibility wrapper around normal root Git.

## Current Status

The collaboration workspace is operational. SQLite-backed task claiming, the LangGraph runner, the autonomous claim loop, integration tests, and multi-gate regression tests exist.

Current validation passes. The next hardening issue is preventing incomplete task metadata from entering `READY`; see `notes/state-machine-guardrails.md` and `notes/command-center-later.md`.

## Git

Use normal Git or the compatibility wrapper:

```bash
git status
MAP_System/scripts/map-git status
```
