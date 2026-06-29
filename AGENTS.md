# Agent Instructions

This repository is organized for file-based multi-agent work. Prefer durable
files over chat memory: task records, shared notes, handoffs, events, and review
artifacts are the source of truth.

## Required Reading

1. `docs/agent-quickstart.md`
2. `docs/project-map.md`
3. The relevant project rules:
   - Reusable system work: `MAP_System/AGENTS.md`
   - Pathwell work: `Projects/Pathwell/AGENTS.md`

## Routing

- Work on the reusable multi-agent framework in `MAP_System/`.
- Work on the Pathwell story project in `Projects/Pathwell/`.
- Treat `archive/`, `logs/`, `.venv/`, `.locks/`, `exports/`, and `snapshots/`
  as non-primary context unless a task explicitly asks for them.

## What Each Folder Answers

| Question | Where to look |
|---|---|
| What are the rules for this project? | `MAP_System/AGENTS.md` |
| What is the current state of the system? | `MAP_System/shared/current-state.md` |
| What decisions have been made? | `MAP_System/shared/decisions.md` |
| How do I author, promote, review, or release a task? | `MAP_System/notes/` |
| How should I communicate with other agents? | `Guidelines/llm-communication-rules.md` then `MAP_System/AGENTS.md` |
| When should I use a local model vs. a core agent? | `MAP_System/notes/local-model-helper-guide.md` |
| What are the general AI collaboration protocols? | `Guidelines/` (universal — applies to any project in this workspace) |
| What does HPOM mean and how does it work? | `MAP_System/shared/hpom.md` |

## Git

Use the provided wrapper from the repository root:

```bash
MAP_System/scripts/map-git status
```

Do not use destructive Git commands unless the user explicitly requests them.
