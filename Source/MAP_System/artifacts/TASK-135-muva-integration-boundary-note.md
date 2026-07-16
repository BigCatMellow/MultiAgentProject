# TASK-135 Integration Boundary Note

task_id: TASK-135
author: codex-lab-muva
created_at: 2026-07-03T16:50:07-04:00
status: support-note
owner: codex-lab-dino

## Finding

ProjectUpdater is a standalone `localStorage` app. CommandCenterUI is a
localhost app with a Python backend. They can be integrated, but the first
slice should keep ProjectUpdater data ownership unchanged.

## Storage Boundary

- Do not read browser `localStorage` from the CommandCenterUI backend.
- Do not serve `Projects/ProjectUpdater/app/index.html` as a new
  CommandCenterUI route unless a storage-origin split is explicitly accepted.
  `file://.../Projects/ProjectUpdater/app/index.html` and
  `http://127.0.0.1:8765/...` use different browser storage origins, so the
  same app may appear to have separate data.
- A read-only status endpoint can safely report static integration facts:
  `available`, `project_dir`, `app_path`, `app_url` or `open_supported`,
  `storage_owner`, and a short `boundary` string.

## Safer First Slice

1. Add `read_project_updater_status()` in CommandCenterUI `app/server.py`.
2. Add `GET /api/project-updater/status` returning static status only.
3. Add a small sidebar panel in `src/chat.html` / `chat.js` / `chat.css`:
   status text, "Open ProjectUpdater" action, and data-boundary note.
4. Prefer opening the existing app location over proxying/hosting the app
   under the CommandCenterUI origin.

## Review Checks

- `python3 -m py_compile /home/home/Projects/CommandCenterUI/app/server.py`
- Endpoint returns JSON and handles missing ProjectUpdater files.
- Existing CommandCenterUI CSRF protection remains unchanged for write/action
  endpoints.
- MAP validators still pass: task graph and events.

