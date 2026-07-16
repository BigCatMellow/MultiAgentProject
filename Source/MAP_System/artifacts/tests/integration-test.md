# Integration Test

Task: TASK-023  
Tester: claude  
Date: 2026-06-19

## Files

- `MAP_System/scripts/integration_test.py` — test runner
- `MAP_System/graph/runner.py` — added `--db` CLI arg (passes db_path into initial state)
- `MAP_System/scripts/agent_loop.py` — `run_runner()` now passes `--db`; `poll_node` `_config` → `config`

## Setup

No manual DB setup required. The test:
1. Creates a temp SQLite DB from `migration/schema.sql`
2. Seeds one `READY` task (`TASK-IT-01`) and one `worker` agent (`test-agent`)
3. Writes a handler script that records `task_id` to a marker file
4. Runs `agent_loop --once` against the temp DB
5. Verifies claim→heartbeat→submit in SQLite
6. Runs `export_to_files` against the temp DB; verifies `tasks/TASK-IT-01.json`
7. Cleans up temp dir and exported task file

## Command

```bash
MAP_System/.venv/bin/python MAP_System/scripts/integration_test.py
```

## Results

```
PASS: agent_loop exited 0
PASS: claimed in stdout
PASS: submitted in stdout
PASS: handler executed
PASS: handler received correct task_id
PASS: task status=SUBMITTED in SQLite
PASS: claimed_by cleared
PASS: lease cleared
PASS: exporter exited 0
PASS: task file exported to tasks/
PASS: exported status=SUBMITTED

11/11 passed — ALL PASS
```

## Notes

- `runner.py --db` added so agent_loop can point the runner subprocess at any DB, not just `map.db`. This enables isolated integration tests and multi-project setups.
- `export_to_files.py --output-dir` added so exporter writes to a temp dir during the test — no real project files (task_graph.json, tasks/, agents/) are mutated. `validate_task_graph` passes immediately after the test.
- Lock files created under `MAP_System/.locks/agent_loop/` during the test; released on exit.
- All temp files (DB, handler script, export output) live under `tempfile.mkdtemp()` and are removed in `finally`.
