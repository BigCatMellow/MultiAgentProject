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
- Use `Guidelines/` as reference material, not as the active task board.
- Treat `archive/`, `logs/`, `.venv/`, `.locks/`, `exports/`, and `snapshots/`
  as non-primary context unless a task explicitly asks for them.

## Git

Use the provided wrapper from the repository root:

```bash
MAP_System/scripts/map-git status
```

Do not use destructive Git commands unless the user explicitly requests them.
