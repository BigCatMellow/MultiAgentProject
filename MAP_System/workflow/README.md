# Workflow

This directory stores machine-readable workflow policy and task graph state.

## Files

- `task_graph.json` - file-backed task graph mirror.
- `workflow.yaml` - workflow definition.
- `runtime_policy.yaml` - runtime routing policy.
- `approval_rules.yaml` - review and approval rules.
- `templates/` - reusable workflow and state snapshot templates.

## Rules

- Keep `task_graph.json` synchronized with `tasks/*.json`.
- Validate changes with `python3 MAP_System/scripts/validate_task_graph.py`.
- Do not edit workflow policy casually to make a task pass; record the decision
  in `shared/decisions.md` when behavior changes.
