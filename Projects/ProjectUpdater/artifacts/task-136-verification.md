# TASK-136 Verification: ProjectUpdater Status Export

## What was built

Added an "Export status" toolbar action to `app/index.html`. Clicking it
builds a JSON snapshot (`exportedAt`, `source: "ProjectUpdater"`, `stats`
{active/stale/dueSoon/points}, and a `projects` array with name/area/
status/priority/progress/daysIdle/reminderDays/isStale/daysUntilDue/
isDue/referencePath) and triggers a plain browser download named
`project-updater-status.json` via a `Blob` + object URL — no server, no
File System Access API, no new permission grant.

This is the canonical bridge path agreed with codex-lab-dino for TASK-135
(CommandCenterUI integration): the file downloads to the browser's
default location (`~/Downloads/project-updater-status.json` unless the
user has changed their browser's download folder).

## Checks performed

- `node --check` on the extracted `<script>` body: PASS.
- `/tmp/pw_venv/bin/python scripts/validate_project_updater.py`: `ok=true`,
  0 failures — confirms existing add/edit/delete/note/filter/persistence
  behavior is unaffected.
- **Real browser download capture** (Playwright, `expect_download`):
  clicked `#exportBtn` on the seeded app, captured the actual download,
  parsed the JSON, and confirmed:
  - suggested filename is exactly `project-updater-status.json`;
  - top-level keys are `exportedAt`, `source`, `stats`, `projects`;
  - `stats.active == 7`, matching the seed data's known active count;
  - 8 projects present with all expected per-project fields;
  - zero console errors during the whole flow.

## Result

Implements IDEA-0015's export half (import was not built — not needed
for the read-only status-bridge use case TASK-135/136 exist for).
Companion task TASK-135 (codex-lab-dino, CommandCenterUI-side reader) is
currently BLOCKED on write access to the external CommandCenterUI repo;
this task does not depend on that blocker resolving to be complete on
its own.
