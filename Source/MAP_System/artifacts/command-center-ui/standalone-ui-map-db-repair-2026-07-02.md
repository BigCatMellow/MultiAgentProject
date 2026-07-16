# CommandCenterUI MAP DB Repair - 2026-07-02

Task context: operator hcom `#16101`, CommandCenterUI standalone bring-up.

## Issue

- `MAP_System/map.db` existed after the repo split but had no task schema/data at startup.
- `MAP_System/.venv/bin/python` was missing, so the requested graph-runner command could not run.
- `python3 MAP_System/graph/runner.py` failed because `langgraph` is not installed in the base interpreter.
- A concurrent `map_task.py create --task-id auto` against the empty DB allocated `TASK-001` and exported one-row mirrors, temporarily clobbering:
  - `MAP_System/tasks/TASK-001.json`
  - `MAP_System/workflow/task_graph.json`
  - `MAP_System/agents/status.json`

## Coordination

- `claude-lab-zaro` owned the CommandCenterUI implementation output paths.
- `codex-lab-lema` owned MAP tracking/DB repair.
- `claude-lab-zaro` restored the clobbered mirrors from committed HEAD before DB rebuild.

## Seeder Fixes

Updated `MAP_System/migration/seed_from_files.py` to tolerate historical file-backed state:

- Events whose `task_id` is not present in the task table now import with `NULL` task_id instead of aborting on a foreign-key failure.
- Approval-gate `required_after` and `resume_on_approval` references are checked against known tasks before insert.
- Events using legacy `timestamp` import that value as DB `created_at`.
- Existing agent status loaded from `agents/status.json` is not overwritten by later task/event references to historical owners.
- Task `output_paths` preserve the file-backed strings instead of normalizing away committed `MAP_System/` prefixes.

Updated `MAP_System/migration/export_to_files.py` so `agents/status.json` exports only agents already present in the status mirror plus agents tied to active tasks. This keeps current live task owners such as `claude-lab-zaro` visible without resurrecting retired session identities from historical task foreign keys.

## Verification

Fresh rebuild command:

```bash
python3 MAP_System/migration/seed_from_files.py --db /tmp/map-rebuild-lema-2.db
```

Rebuild result:

- `tasks`: 75
- max numeric task ID: 85
- statuses: `APPROVED=16`, `DONE=25`, `RELEASED=34`
- `TASK-001` output paths were restored to the original bootstrap review paths only.

Live DB replacement:

```bash
install -m 0644 /tmp/map-rebuild-lema-2.db MAP_System/map.db
```

Post-replacement checks:

- live `MAP_System/map.db` has `tasks=75`, max ID `85`
- `python3 MAP_System/scripts/validate_task_graph.py` passed
- `python3 MAP_System/scripts/validate_events.py` returned `errors=0`, historical warnings only
- `python3 MAP_System/scripts/validate_shared_state.py` passed

## Handoff

`claude-lab-zaro` recreated the CommandCenterUI task as `TASK-086`. After implementation, review, and release, the live DB and mirrors show:

- total tasks: 76
- max numeric task ID: 86
- `TASK-086`: `RELEASED`

Review and release artifacts:

- `MAP_System/artifacts/reviews/task086-review-lema.md`
- `MAP_System/artifacts/releases/task-086-release-checklist.md`
