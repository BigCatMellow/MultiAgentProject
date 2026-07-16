# Operations Runbook

Use these commands from the repository root unless noted otherwise.

## Status

```bash
python3 MAP_System/scripts/map_status.py
```

Check Git state:

```bash
git status
MAP_System/scripts/map-git status
```

## Validation

Validate task graph shape:

```bash
python3 MAP_System/scripts/validate_task_graph.py
```

Run the MAP test suite:

```bash
MAP_System/scripts/run_tests.sh
```

Current baseline: validation passes. If validation fails, check the reported
task IDs first and use `notes/task-metadata-repair-plan.md` for metadata repair.

## Runner

Inspect the next route without writing events:

```bash
MAP_System/.venv/bin/python MAP_System/graph/runner.py --pretty
```

Record the chosen route explicitly:

```bash
MAP_System/.venv/bin/python MAP_System/graph/runner.py --pretty --record-event
```

## Agent Loop

Dry-run a single autonomous loop cycle:

```bash
MAP_System/.venv/bin/python MAP_System/scripts/agent_loop.py --once --dry-run
```

Use handler commands only as trusted operator configuration. The handler string
is shell-executed after `{task_id}` substitution.

## Repair Checklist

When MAP looks inconsistent:

1. Read `shared/current-state.md`.
2. Run `python3 MAP_System/scripts/map_status.py`.
3. Run `python3 MAP_System/scripts/validate_task_graph.py`.
4. Compare task JSON with `workflow/task_graph.json`.
5. Check recent `events/events.jsonl` entries.
6. Create or update a handoff if another agent must continue.
