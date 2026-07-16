# LangGraph Scaffold

LangGraph should orchestrate the workflow, not replace project storage.

In this workspace:

- canonical task records live in `tasks/` and `workflow/task_graph.json`;
- durable project truth lives in `shared/`;
- artifacts live in `artifacts/`;
- events live in `events/events.jsonl`;
- LangGraph code should load state from those files, route the next action, and write results back through explicit project operations.

## Intended Graph

```text
load_task_graph
  -> load_runtime_policy
  -> load_agent_status
  -> scan_helper_notes
  -> evaluate_tasks
  -> choose_route
      -> review
      -> wait_for_agent
      -> propose_helper
      -> claim_or_assign
      -> wait_or_reconcile
```

## What To Implement Next

`TASK-002` should add a minimal runner that:

1. loads `workflow/task_graph.json`;
2. computes which tasks are ready based on dependency statuses;
3. prints or records the next route;
4. keeps all canonical task state in files until SQLite is introduced.

## Current Runner

Run the executable graph from the project root:

```bash
langgraph-run
```

or directly:

```bash
MAP_System/.venv/bin/python MAP_System/graph/runner.py --pretty
```

The runner uses LangGraph's `StateGraph` to:

- load `workflow/task_graph.json`;
- load `workflow/runtime_policy.yaml`;
- load `agents/status.json`;
- scan temporary helper notes in `inbox/helpers/`;
- compute dependency-satisfied ready tasks;
- route submitted tasks to `review`;
- route tasks that explicitly require an unavailable agent to `wait_for_agent`;
- route helper-suitable ready tasks to `propose_helper` when helper policy allows capacity;
- route ready tasks to `claim_or_assign`;
- route idle workflows to `wait_or_reconcile`.

By default it is read-only. It does not mutate task records, project state, helper state, or event logs.

To explicitly record the selected route in the event log:

```bash
MAP_System/.venv/bin/python MAP_System/graph/runner.py --pretty --record-event
```

The runner never launches helper agents automatically. When it selects `propose_helper`, it returns a command-center hint such as:

```bash
ai helper start codex task-001 "Assist with TASK-001; read the task file, keep MAP_System/inbox/helpers/ updated, and report findings."
```

This keeps LangGraph as the dispatcher while the command center and core agents remain accountable for starting, monitoring, and stopping helpers.

## Unavailable Agents

Agent availability is tracked in `agents/status.json`.

Use command-center commands to update it:

```bash
ai agent standby gemini "manual_operator_coordination" "when operator prompts it"
ai agent available gemini
ai agent list
```

Available agents should continue work while an agent is on standby. LangGraph only routes to `wait_for_agent` when a ready task explicitly includes a field such as:

```json
"required_agent": "gemini"
```

Gemini and Antigravity may need manual operator prompting before they begin work. Treat their status as planning state, not proof that hcom communication is sufficient.
