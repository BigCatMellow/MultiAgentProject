# SQLite Seed Script Test

Task: TASK-013  
Tester: codex  
Date: 2026-06-19

## Commands

```bash
python3 -m py_compile MAP_System/migration/seed_from_files.py
python3 MAP_System/migration/seed_from_files.py
python3 MAP_System/migration/seed_from_files.py
python3 -c "import sqlite3; c=sqlite3.connect('MAP_System/map.db'); ..."
```

The `sqlite3` shell is not installed in this environment, so verification used Python's standard `sqlite3` module.

## Result

The script created `MAP_System/map.db`, applied the schema, and seeded current file-backed state.

Final repeat-run summary:

```text
Seeded /home/home/Downloads/MultiAgentProject/MAP_System/map.db
Seed summary:
  agents: inserted=0 skipped=42
  approval_gate_resume_tasks: inserted=0 skipped=2
  approval_gates: inserted=0 skipped=1
  artifacts: inserted=0 skipped=4
  decisions: inserted=0 skipped=8
  events: inserted=0 skipped=25
  task_acceptance_criteria: inserted=0 skipped=54
  task_dependencies: inserted=0 skipped=3
  task_output_paths: inserted=0 skipped=66
  tasks: inserted=0 skipped=13
```

Verified table list:

```text
agents
approval_gate_resume_tasks
approval_gates
artifact_versions
artifacts
decisions
events
helpers
messages
review_findings
reviews
task_acceptance_criteria
task_dependencies
task_output_paths
tasks
```

Verified row counts:

```text
agents=6
tasks=13
task_dependencies=3
task_output_paths=66
task_acceptance_criteria=54
events=25
decisions=8
artifacts=4
approval_gates=1
```

`TASK-013` status in SQLite after the final run: `SUBMITTED`.

## Notes

- Event seeding uses an explicit existence check because SQLite unique constraints allow duplicate rows when any indexed value is `NULL`.
- The script creates stub agent rows for event senders that are not present in `agents/status.json`, such as `command-center` and `langgraph-runner`, so foreign keys remain valid.
