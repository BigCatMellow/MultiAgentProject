# TASK-038 Release Gate Test

Date: 2026-06-29
Owner: codex-live

## Scope

Verified HPOM-006 release gating: `APPROVED` means review passed, while `RELEASED` requires a completed release checklist and durable release record.

## Commands

```bash
python3 MAP_System/tests/test_release_gate.py
python3 -m py_compile MAP_System/scripts/release_task.py MAP_System/scripts/map_task.py MAP_System/tests/test_release_gate.py MAP_System/scripts/validate_task_graph.py
python3 MAP_System/scripts/validate_task_graph.py
MAP_System/scripts/run_tests.sh
```

## Results

- Incomplete checklist blocks release and leaves task status `APPROVED` with no `task_release_records` row.
- `release_task.py` with a completed checklist records a release and moves the task to `RELEASED`.
- `map_task.py release` delegates through the same gate and moves the task to `RELEASED`.
- `task_release_records` was added to the live `MAP_System/map.db`.
- Full MAP test wrapper passed with `SUMMARY pass=9 fail=0 total=9`.
