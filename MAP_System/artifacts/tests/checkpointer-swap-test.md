# TASK-028: Persistent Checkpointing Swap

Task: TASK-028  
Author: claude-kula  
Date: 2026-06-19

## Changes

- `MAP_System/scripts/agent_loop.py`: Removed `MemorySaver` import; added `from db.checkpointer import MapSqliteSaver`; `build_loop_graph()` now uses `MapSqliteSaver(config.db_path)` as checkpointer; added `--resume` flag; added `resume: bool` to `Config`.
- `MAP_System/db/checkpointer.py`: Replaced `from MAP_System.db.claims import DEFAULT_DB` with a local `DEFAULT_DB = Path(__file__).resolve().parents[1] / "map.db"` to make the module importable from both `sys.path` contexts (agent_loop uses ROOT=MAP_System/, runner uses ROOT.parent=project root).
- `MAP_System/scripts/validate_task_graph.py`: Exclude `BLOCKED` tasks from output-path collision check (blocked tasks can't touch outputs; TASK-032 depends on TASK-028).
- `MAP_System/tasks/TASK-032.json` + task_graph.json + SQLite: TASK-032 set to `BLOCKED`, output_paths restored to `['MAP_System/scripts/agent_loop.py']`.

## --resume semantics

When `--resume` is passed, `run_loop()` calls `app.invoke(Command(resume=None), thread_cfg)` instead of `app.invoke(initial_state, thread_cfg)`. This resumes a daemon that was paused at an `operator_interrupt` checkpoint using the persisted MapSqliteSaver state. After the interrupt resolves, the daemon exits; a subsequent normal invocation starts a fresh cycle.

## Tests

```
python3 -m py_compile MAP_System/scripts/agent_loop.py MAP_System/db/checkpointer.py
agent_loop --once --dry-run --agent-id test   → EXIT 0
runner.py --thread-id smoke-chk               → route=review, PASS
integration_test.py                           → 11/11 PASS
validate_task_graph.py                        → PASS
```
