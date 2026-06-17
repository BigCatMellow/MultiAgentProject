# MultiAgentProject

This workspace is set up for collaboration between Codex, Claude Code, and a future LangGraph runtime.

The first working rule is simple: agents coordinate through durable files, task records, inbox notes, handoffs, and review artifacts instead of relying on one long shared chat.

All paths below are relative to `MAP_System/` unless stated otherwise.

## Start Here

1. Read `AGENTS.md`.
2. Read `shared/project_brief.md`.
3. Pick or receive a task from `tasks/`.
4. Record progress in `events/events.jsonl` and agent-specific inbox/handoff files when needed.
5. Submit finished work as an artifact and request independent review.

## Important Paths

- `AGENTS.md` - shared operating rules for all agents.
- `CLAUDE.md` - Claude Code entrypoint; points back to the shared rules.
- `shared/` - project truth, decisions, requirements, and unresolved questions.
- `workflow/` - task graph, runtime policy, approval rules, and LangGraph notes.
- `tasks/` - one JSON file per task.
- `artifacts/` - durable work products.
- `inbox/` - direct agent-to-agent notes.
- `handoffs/` - structured handoff packets.
- `langgraph/` - starter orchestration code and notes.
- `scripts/validate_task_graph.py` - mechanical task graph validator.
- `scripts/map-git` - Git wrapper for this workspace while `.git` is blocked by a read-only mount.

## Current Status

The collaboration workspace is bootstrapped. The LangGraph code is a scaffold, not a running autonomous system yet. The next implementation task is to turn the file-backed task graph into a minimal executable LangGraph flow.

## Git

Use `scripts/map-git` instead of plain `git` in this workspace:

```bash
MAP_System/scripts/map-git status
```
