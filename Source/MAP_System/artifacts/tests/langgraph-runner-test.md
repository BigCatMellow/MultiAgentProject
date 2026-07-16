# LangGraph Runner Test

Command:

```bash
python3 MAP_System/langgraph/runner.py --pretty
```

or, with the project virtual environment:

```bash
MAP_System/.venv/bin/python MAP_System/langgraph/runner.py --pretty
```

Expected behavior:

- loads `MAP_System/workflow/task_graph.json`;
- loads `MAP_System/workflow/runtime_policy.yaml`;
- loads `MAP_System/agents/status.json`;
- scans helper notes from `MAP_System/inbox/helpers/`;
- computes `ready_tasks` from task status and satisfied dependencies;
- routes `SUBMITTED` tasks to `review`;
- routes ready tasks with `required_agent` set to an unavailable agent to `wait_for_agent`;
- routes helper-suitable ready work to `propose_helper` when helper capacity is available;
- routes other ready work to `claim_or_assign`;
- routes idle workflows to `wait_or_reconcile`;
- reports `recommended_action`, `command_hint`, `available_agents`, `unavailable_agents`, `helper_candidate_tasks`, and `helper_capacity`.

The default runner is read-only. It does not rewrite task JSON, project state, helper notes, or event logs.

Event recording is explicit:

```bash
MAP_System/.venv/bin/python MAP_System/langgraph/runner.py --pretty --record-event
```

That command appends a routing event to `MAP_System/events/events.jsonl`.
