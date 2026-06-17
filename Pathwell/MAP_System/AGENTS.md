# Agent Operating Rules

These rules apply to Codex, Claude Code, and any future worker agent in this workspace.

## Core Protocol

1. Work only on an assigned or explicitly claimed task from `tasks/`.
2. Read `shared/project_brief.md`, `shared/requirements.md`, `shared/decisions.md`, and the task file before editing.
3. Keep one accountable owner per active task.
4. Do not silently modify another active task's owned output paths.
5. Record important assumptions in `shared/unresolved_questions.md` or `shared/decisions.md`.
6. Put durable work in `artifacts/`, `shared/`, `workflow/`, `tasks/`, or source files, not only in chat.
7. Use `events/events.jsonl` for short append-only activity records.
8. Use `handoffs/` for work that another agent should review or continue.
9. Do not approve your own substantive deliverable.
10. Stop when the task acceptance criteria are met.

## Git Protocol

The `.git` path is currently occupied by a read-only mount point, so normal Git commands do not work in this workspace yet.

Use the project wrapper instead:

```bash
scripts/map-git status
scripts/map-git diff
scripts/map-git add .
scripts/map-git commit -m "Describe the change"
```

From the repository root, use:

```bash
MAP_System/scripts/map-git status
```

See `notes/git_setup.md` for details.

## Communication

Prefer structured messages:

- `PROGRESS`
- `QUESTION`
- `ANSWER`
- `BLOCKED`
- `HANDOFF`
- `SUBMISSION`
- `REVIEW_REQUESTED`
- `CHANGES_REQUESTED`
- `APPROVED`
- `DECISION_PROPOSED`
- `DECISION_RECORDED`

Use this compact event shape in `events/events.jsonl`:

```json
{"created_at":"2026-06-17T00:00:00-04:00","type":"PROGRESS","task_id":"TASK-001","sender":"codex","summary":"Short factual update","artifact_paths":[]}
```

## Handoff Format

Create a Markdown file in `handoffs/` named like:

```text
HANDOFF-TASK-001-codex-to-claude.md
```

Include:

- task ID
- sender
- intended recipient
- status
- files changed or created
- what needs review or continuation
- known limitations

## File Ownership

Task files list `output_paths`. Treat those as owned by the task while it is active. If ownership needs to change, create a handoff and update the task status.

## Review Standard

Review findings should be concrete and actionable. Use severities:

- `BLOCKER`
- `REQUIRED`
- `RECOMMENDED`
- `OPTIONAL`

Only `BLOCKER` and `REQUIRED` findings should block approval.
