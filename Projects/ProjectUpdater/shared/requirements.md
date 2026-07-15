<!-- hpom: file: shared/requirements.md -->
<!-- hpom: project: ProjectUpdater -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: bootstrap -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Requirements — ProjectUpdater

## Functional

- Dashboard: active/stale/due-soon/points stat tiles, a "needs attention"
  list (stale projects sorted by days idle), and a recent-notes feed.
- Projects view: filterable list (Open / Stale / Due soon / Finished /
  Archived / All) showing goal, next action, progress, priority, points,
  streak, and last-visited.
- Project management: edit an existing project after creation; delete a
  project with confirmation; preserve existing notes when renaming a project
  and remove related notes when deleting that project.
- Goals: support multiple goal lines per project while migrating older
  single-goal `localStorage` records without data loss.
- Project reference: store an optional folder path for each project and expose
  an `Open folder` action from project cards. The action uses a `file://` URL
  against the stored path and must not add a backend, execute local processes,
  or copy shell commands.
- Quick Note view: pick an existing project, log a note (type: Note /
  Idea / Decision / Blocker / Next Action, optional energy level), update
  next action/status/progress, and reset the idle clock (or just mark
  visited without a full note).
- Add Project view: name, area, one or more goals, next action, priority,
  project folder path, reminder window (days), optional due date.
- Reminder banner on the dashboard when stale projects exist.
- Export status: a toolbar action that downloads a `project-updater-status.json`
  snapshot (stats + per-project status) via a plain browser download — no
  server, no file-system-write API, no new permission grant. This is the
  bridge other tools (e.g. CommandCenterUI, TASK-135/136) can read from; it
  does not create a live connection, only a manual, user-triggered export.

## Non-functional

- Works fully offline after first load (no network calls).
- Responsive down to a phone-width viewport (the functional prototype
  already had mobile breakpoints worth keeping).
- No data loss on reload — every write persists to `localStorage`
  immediately.
- Single HTML entry point; no build tooling required to run it.

## Quality bar

- Manually or validator exercised end-to-end (add a project, edit it, add
  goals/folder-reference data, add a note, delete a project, watch status/filter
  behavior, check open-folder behavior, reload the page and confirm data
  survived) before the task is submitted for review.
