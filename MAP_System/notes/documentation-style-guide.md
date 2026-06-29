# Documentation Style Guide

This guide applies to all MAP Markdown and template files.

## Principle

Write for agents first.

MAP files should be easy to scan, reference, diff, compact, and promote into
other files. Prefer structured records over narrative prose.

## Default Style

Use:

- short headings;
- stable IDs;
- explicit status labels;
- file paths;
- task IDs;
- thread IDs when communication is involved;
- bullets;
- compact tables when they improve scanning;
- links to canonical outcome locations.

Avoid:

- long paragraphs;
- repeated background;
- vague phrases;
- unlinked references;
- hidden assumptions;
- updates that do not name an owner, task, status, or output path.

## Required Fields When Relevant

For any durable note, include the relevant subset:

- Task: `TASK-NNN`
- Thread: `THREAD-...`
- Status: `open | pending | blocked | approved | closed`
- Owner: `[agent-id]`
- Source paths: `[path]`
- Output paths: `[path]`
- Outcome location: `[path | pending]`
- Follow-up: `[task/path/owner | none]`

## Complete Sentences

Use complete sentences only when they clarify:

- risk;
- tradeoff;
- exception;
- conflict;
- reasoning behind a decision.

For normal state, use terse fields and bullets.

## Good Pattern

```md
## TASK-048 Metadata Repair

- Status: `open`
- Owner: `codex`
- Source paths: `tasks/TASK-048.json`, `events/events.jsonl`
- Output paths: `tasks/TASK-048.json`, `workflow/task_graph.json`
- Follow-up: run `python3 MAP_System/scripts/validate_task_graph.py`
```

## Poor Pattern

```md
We looked at the task and noticed some things were missing, so someone should
probably clean it up later when they have time.
```

## File-Specific Notes

- `shared/` files should describe current truth.
- `tasks/` files should define executable work.
- `notes/` files should describe repeatable procedures.
- `artifacts/` files should record historical evidence.
- `handoffs/` files should transfer responsibility.
- `inbox/` files should carry scoped messages.
- `archive/` files should preserve compacted history.

## Cross-Reference Rule

If a file depends on another file for meaning, link or name that file directly.

Examples:

- A review names the task and output paths.
- A helper note names the owning core agent.
- A compaction summary names source files and active files updated.
- A decision names the question or task that produced it.

## Maintenance

When editing an existing file:

1. Prefer adding a short structured section over appending prose.
2. Remove or archive stale narrative if it conflicts with current truth.
3. Preserve raw history in `events/`, `artifacts/`, `handoffs/`, or `archive/`.
4. Update indexes when adding a new durable memory file.

## Pushback Notes

Documentation changes should be challenged when they:

- create new memory without changing behavior;
- duplicate an existing guide;
- make active context longer without making it clearer;
- bury ownership, status, paths, or acceptance criteria in prose;
- compact by deleting raw evidence.

Safer alternative:

- add a structured section to an existing file;
- link to the canonical file;
- archive historical detail and summarize forward;
- create a task for implementation instead of documenting speculative behavior.
