# Task Metadata Repair Plan

Use this plan to repair the approved tasks that currently break task graph
validation.

## Problem

The validator requires every task to have:

- at least one `acceptance_criteria` entry;
- at least one `output_paths` entry.

Common gaps:

- task has empty acceptance criteria;
- task has empty output paths;
- task files and `workflow/task_graph.json` disagree;
- SQLite metadata tables do not match file-backed task records.

## Safety Rule

Do not invent new scope just to satisfy the validator.

Repair metadata by reading the task description, generated outputs, related
project files, event log entries, and review artifacts. The repaired criteria
should describe what the task already intended to produce.

## Repair Process

1. Read the task JSON.
2. Find related outputs in project files, `artifacts/`, `events/events.jsonl`,
   and any relevant handoffs.
3. Add concrete `output_paths` for files the task created or modified.
4. Add acceptance criteria that a reviewer can verify from those outputs.
5. Update both `tasks/TASK-NNN.json` and `workflow/task_graph.json`.
6. Run `python3 MAP_System/scripts/validate_task_graph.py`.
7. Run `MAP_System/scripts/run_tests.sh`.

## Suggested Criteria Shape

For extraction tasks:

- output chapter files exist at the named paths;
- content boundaries match the source description;
- leading and trailing blank lines are stripped;
- source text is not otherwise rewritten.

For writing/revision tasks:

- output chapter or scene file exists at the named path;
- required scene beats from the task description are present;
- relevant story constraints or voice files were considered;
- review artifact or event record documents completion.

For maintenance tasks:

- named files or state records were updated;
- validation command passes, or any remaining failure is documented;
- event or artifact records the change.

## Do Not Use

Avoid vague criteria such as:

- "Improve chapter quality."
- "Make it better."
- "Finish the task."
- "Looks good."

Criteria should be observable from files, commands, or review records.
