# map-task Test

Task: TASK-033  
Tester: codex  
Date: 2026-06-19

## Commands

```bash
python3 -m py_compile MAP_System/scripts/map_task.py
```

Temp DB fixture:

```text
create 0 ... {"created":"T-NEW"}
approve 0 ... {"task_id":"T-NEW","status":"APPROVED"}
reject 0 ... {"task_id":"T-REJ","status":"CHANGES_REQUESTED"}
bad 1 error: BASE is APPROVED, not SUBMITTED
```

## Coverage

- `create` inserts task metadata, dependencies, output paths, criteria, event, and synced file mirror.
- `show` prints DB-backed task JSON.
- `approve` requires `SUBMITTED`, sets `APPROVED`, emits event, syncs files.
- `reject` requires `SUBMITTED`, sets `CHANGES_REQUESTED`, emits event, syncs files.
- Bad state exits nonzero with a clear error.
- Fixture uses `--output-dir` and `--event-log` under temp storage; project files are not mutated.
