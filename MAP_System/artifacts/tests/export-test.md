# SQLite Export Test

Task: TASK-018
Tester: codex
Date: 2026-06-19

## Commands

```bash
python3 -m py_compile MAP_System/migration/export_to_files.py
python3 MAP_System/migration/seed_from_files.py
python3 MAP_System/migration/export_to_files.py --dry-run
python3 MAP_System/migration/export_to_files.py
python3 MAP_System/migration/export_to_files.py
```

## Results

Dry run before canonical export:

```text
mode=dry_run
files_written=22
files_unchanged=0
```

First export:

```text
mode=written
files_written=22
files_unchanged=0
```

Repeat export:

```text
mode=written
files_written=0
files_unchanged=22
```

Verified:

- Task JSON files are regenerated from SQLite task rows.
- `workflow/task_graph.json` is regenerated from SQLite task rows, dependencies, output paths, and acceptance criteria.
- `agents/status.json` is regenerated from SQLite agent rows while excluding system agents.
- Existing task `input_paths` are preserved from task files because the current SQLite schema does not store them.
- Re-running export is idempotent when SQLite and files are already in sync.
