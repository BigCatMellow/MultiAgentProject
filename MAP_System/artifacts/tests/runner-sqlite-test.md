# Runner SQLite Test

Task: TASK-015  
Tester: codex  
Date: 2026-06-19

## Commands

```bash
python3 -m py_compile MAP_System/langgraph/runner.py
python3 MAP_System/migration/seed_from_files.py
MAP_System/.venv/bin/python MAP_System/langgraph/runner.py --pretty
python3 -c "move MAP_System/map.db aside; run runner; restore MAP_System/map.db"
MAP_System/.venv/bin/python MAP_System/langgraph/runner.py --record-event --pretty
python3 -c "temporarily alter SQLite TASK-015 status; run runner; restore MAP_System/map.db"
```

## SQLite Read Path

With `MAP_System/map.db` present, the runner loaded tasks and agents from SQLite:

```text
"events": [
  "loaded tasks from map.db",
  "loaded workflow/runtime_policy.yaml",
  "loaded agents from map.db",
  "scanned 0 helper notes",
  "evaluated 16 tasks",
  "routed workflow to wait_or_reconcile"
]
```

The summary reported:

```text
in_progress_tasks=["TASK-015", "TASK-016"]
available_agents=["claude", "codex"]
unavailable_agents=["antigravity", "gemini"]
done_task_ids includes TASK-001 through TASK-014
```

## JSON Fallback

The test temporarily moved `MAP_System/map.db` aside in a `try/finally` script and restored it immediately after the runner completed.

Fallback succeeded and loaded from file-backed state:

```text
"events": [
  "loaded /home/home/Downloads/MultiAgentProject/MAP_System/workflow/task_graph.json",
  "loaded workflow/runtime_policy.yaml",
  "loaded agents/status.json",
  "scanned 0 helper notes",
  "evaluated 16 tasks",
  "routed workflow to wait_or_reconcile"
]
```

## SQLite Event Recording

Before `--record-event`, SQLite had 29 events. After running:

```bash
MAP_System/.venv/bin/python MAP_System/langgraph/runner.py --record-event --pretty
```

SQLite had 30 events, and the newest row was:

```text
('PROGRESS', 'langgraph-runner', 'Routed workflow to wait_or_reconcile: No dependency-satisfied ready work found; reconcile stale claims or wait.')
```

The same event was appended to `MAP_System/events/events.jsonl`.

## SQLite Source Override

To prove the runner preferred SQLite over JSON, the test temporarily changed only the SQLite `TASK-015` row from `IN_PROGRESS` to `READY`, leaving the JSON task files unchanged. The runner then reported:

```text
next_route="claim_or_assign"
ready_tasks=["TASK-015"]
in_progress_tasks=["TASK-016"]
"loaded tasks from map.db"
```

The original database was restored immediately after the test.
