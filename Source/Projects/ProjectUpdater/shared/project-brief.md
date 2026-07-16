<!-- hpom: file: shared/project-brief.md -->
<!-- hpom: project: ProjectUpdater -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: bootstrap -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Project Brief — ProjectUpdater

## Objective

Build a working implementation of the "Project Updater" design (a
personal project/task tracker) sourced from a Claude Design project:
`https://claude.ai/design/p/9e3f5e32-b481-4f33-8091-67f8b3456daf?file=Project+Updater.dc.html`.

The app should let a single user:

- see a dashboard of active/stale/due-soon projects and recent notes;
- browse and filter all projects (open, stale, due soon, finished,
  archived);
- capture a quick note against a project (resets its idle clock, can
  update status/progress);
- add a new project with a goal, next action, priority, reminder window,
  and optional due date.

## Completion condition

- All four views (Dashboard, Projects, Quick Note, Add Project) are
  implemented and functional against real, persisted data (not sample
  data).
- Stale detection (`daysIdle >= reminderDays`) and due-soon detection
  (due within 7 days) work correctly against real dates, not hardcoded
  sample values.
- Data survives a page reload (persisted in `localStorage`).
- Visual design matches the dark theme from `Project Updater.dc.html`
  (colors, layout, typography) reasonably closely — this is a personal
  tool, not a pixel-perfect handoff.
- No server/backend dependency; runs by opening the HTML file directly.

## Non-goals

- No multi-user support, accounts, or sync.
- No mobile-native app; a responsive web page is sufficient.
- Not replicating the Google-Apps-Script-specific backend from the
  earlier prototype — its data model and UI logic are reused, its
  `google.script.run` calls are not.
