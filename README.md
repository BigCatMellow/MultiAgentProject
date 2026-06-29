# MultiAgentProject

This workspace contains a reusable multi-agent coordination system and one
active project that uses it.

## Start Here

- `AGENTS.md` - root instructions for AI agents.
- `docs/agent-quickstart.md` - short agent onboarding checklist.
- `docs/project-map.md` - directory map and working conventions.
- `MAP_System/README.md` - reusable MAP system overview.
- `Projects/Pathwell/README.md` - Pathwell project overview.

## Top-Level Layout

```text
MAP_System/          Reusable multi-agent project system.
Projects/Pathwell/   Active writing project with its own project-local MAP state.
Projects/Backups/    Dated backups and preserved project snapshots.
Guidelines/          General AI collaboration and prompt/local-model guidelines.
docs/                Human and agent navigation docs for this workspace.
launchers/           Desktop launcher files for local agent terminals.
archive/             Retired scratch files that should not be active inputs.
```

## Common Commands

Use the workspace Git wrapper instead of plain `git`:

```bash
MAP_System/scripts/map-git status
```

Validate the reusable MAP task graph:

```bash
python3 MAP_System/scripts/validate_task_graph.py
```

Validate the Pathwell task graph:

```bash
cd Projects/Pathwell
python3 MAP_System/scripts/validate_task_graph.py
```
