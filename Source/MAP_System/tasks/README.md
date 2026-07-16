# Tasks

This directory contains one JSON file per MAP task. Task files are the executable
work queue and must stay synchronized with `workflow/task_graph.json`.

## Required Quality Bar

Every task should include:

- `task_id`
- `title`
- `status`
- `dependencies`
- `owner`
- `description`
- `input_paths`
- `output_paths`
- `acceptance_criteria`

Do not create new tasks with empty `output_paths` or empty
`acceptance_criteria`. If the output is not a file, name the durable artifact,
event, decision, or verification record that proves the task is complete.

## Authoring Help

See `../notes/task-authoring-guide.md`.
