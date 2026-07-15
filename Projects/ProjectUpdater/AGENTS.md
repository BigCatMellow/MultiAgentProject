# Agent Instructions — ProjectUpdater

Follow the root `AGENTS.md` and `MAP_System/AGENTS.md` as the canonical
collaboration protocol. This file adds project-specific notes only.

## Scope

ProjectUpdater is a standalone, client-side personal project-tracking web
app (dashboard, project list, quick-note capture, add-project form) with
stale/due-soon detection. It has no server backend; data persists in the
browser via `localStorage`.

## Decision paths

- Routine implementation, bug fixes, and UI adjustments: core agent
  decides and records directly (ARCHITECTURE/OWNERSHIP class per
  `MAP_System/DECISION_CLASSES.md`).
- Changing the data model in a way that breaks existing saved
  `localStorage` data, or adding any server/network dependency: escalate
  to command-center first (SCOPE class, since it changes what the app is
  allowed to depend on).

## Source design artifacts

- `artifacts/design/project-updater.dc.html` — visual design reference
  (Claude Design component, sample data only, no persistence).
- `artifacts/design/project-updater-prototype.html` — earlier functional
  prototype (Google Apps Script backend); its data model and interaction
  logic (notes, stale/due detection, filters) are reused, its backend
  calls are not.
