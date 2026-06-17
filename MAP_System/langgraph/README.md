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
  -> find_ready_tasks
  -> claim_or_wait
  -> execute_task
  -> submit_artifact
  -> review_required?
      -> review
      -> changes_requested -> revise
      -> approved -> integrate
  -> update_project_state
```

## What To Implement Next

`TASK-002` should add a minimal runner that:

1. loads `workflow/task_graph.json`;
2. computes which tasks are ready based on dependency statuses;
3. prints or records the next route;
4. keeps all canonical task state in files until SQLite is introduced.

