# TASK-135 ProjectUpdater + CommandCenterUI Integration Plan

Owner: codex-lab-dino
Date: 2026-07-03

## Current State

- ProjectUpdater lives in this repo at `Projects/ProjectUpdater/`.
- CommandCenterUI lives outside this repo at `/home/home/Projects/CommandCenterUI`.
- CommandCenterUI is the right integration host because it already has a
  localhost Python backend and live sidebar UI.
- ProjectUpdater remains a standalone static app whose data is owned by browser
  `localStorage`; CommandCenterUI cannot safely read that data directly.

## Proposed First Integration

Add a CommandCenterUI sidebar section called `ProjectUpdater` that:

- shows whether the ProjectUpdater app file exists;
- shows the local app path;
- shows whether a manually exported ProjectUpdater status snapshot exists;
- links to/open ProjectUpdater through a local `file://` URL;
- states the data boundary clearly: project records live in ProjectUpdater's
  browser `localStorage`; CommandCenterUI can launch/status-check it, but cannot
  inspect saved ProjectUpdater projects until an explicit import/export or shared
  storage bridge exists.

This satisfies the operator's "integrate" request without inventing a risky
cross-app storage layer.

## Intended CommandCenterUI Edits

Files outside this repo:

- `/home/home/Projects/CommandCenterUI/app/server.py`
- `/home/home/Projects/CommandCenterUI/src/chat.html`
- `/home/home/Projects/CommandCenterUI/src/chat.js`
- `/home/home/Projects/CommandCenterUI/src/chat.css`
- `/home/home/Projects/CommandCenterUI/README.md`

Server endpoint:

```text
GET /api/project-updater/status
```

Response shape:

```json
{
  "ok": true,
  "project_dir": "/home/home/Projects/MultiAgentProject/Projects/ProjectUpdater",
  "app_path": "/home/home/Projects/MultiAgentProject/Projects/ProjectUpdater/app/index.html",
  "app_exists": true,
  "app_url": "file:///home/home/Projects/MultiAgentProject/Projects/ProjectUpdater/app/index.html",
  "status_export_path": "/home/home/Downloads/project-updater-status.json",
  "status_export_exists": false,
  "status_export": null,
  "data_owner": "ProjectUpdater browser localStorage",
  "can_read_projects": false
}
```

UI placement:

- Add a small `ProjectUpdater` card below the existing MAP summary in the
  CommandCenterUI sidebar.
- Include an `Open ProjectUpdater` link/button pointing at `app_url`.
- Include exported counts/list data only if
  `/home/home/Downloads/project-updater-status.json` exists and validates.
- Include one concise boundary line: `Saved ProjectUpdater records live in that
  browser's localStorage.`

## Export Bridge

Valo is implementing the ProjectUpdater export side. Preferred bridge path:

```text
/home/home/Downloads/project-updater-status.json
```

Rationale:

- ProjectUpdater is a static browser app; downloading a JSON snapshot is honest
  and requires no backend.
- CommandCenterUI can read the exported file through its existing localhost
  backend.
- Writing directly into CommandCenterUI runtime from the browser would require a
  user-granted File System Access flow and is unnecessary for the first slice.

## Deferred Integration

True data integration should be a later task because it needs an explicit data
contract:

- ProjectUpdater export/import JSON;
- a shared file-backed store;
- or a CommandCenterUI import action that the operator intentionally triggers.

Do not silently scrape browser profiles or assume access to a browser
`localStorage` database.

## Validation Plan

Before submit:

```bash
python3 -m py_compile /home/home/Projects/CommandCenterUI/app/server.py
curl -s http://127.0.0.1:8765/api/project-updater/status
python3 -m py_compile Projects/ProjectUpdater/scripts/validate_project_updater.py
/tmp/pw_venv/bin/python Projects/ProjectUpdater/scripts/validate_project_updater.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py
MAP_System/scripts/run_tests.sh
```

If the CommandCenterUI server is not running, start it with:

```bash
/home/home/Projects/CommandCenterUI/run-command-center-app.sh --server-only
```

## Current Blocker

The Codex workspace can read `/home/home/Projects/CommandCenterUI`, but it is
outside the current writable roots. Escalation requests to allow edits there
were rejected by the sandbox reviewer because the current session is in a
usage-limit state. No workaround was attempted.

Needed before implementation:

- explicit operator approval for writing to `/home/home/Projects/CommandCenterUI`;
  or
- a writable-root/session update that includes that project; or
- direction to keep TASK-135 as a planning-only task until a later session.
