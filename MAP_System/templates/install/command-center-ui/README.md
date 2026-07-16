# CommandCenterUI

CommandCenterUI is the graphical MAP command-center app bundled by the MAP
fresh installer.

The installer places this directory at `~/Projects/CommandCenterUI` by default
and installs a `command-center-ui` launcher in `~/.local/bin`. That launcher
sets `COMMAND_CENTER_UI_WORKSPACE` to the current MAP checkout before starting
the app, so the UI does not depend on a hard-coded workstation path.

## Run

```bash
command-center-ui
```

Or, from this directory:

```bash
./run-command-center-app.sh
./run-command-center-app.sh --server-only
```

The app starts a localhost backend on `127.0.0.1:8765`, opens a native
GTK/WebKit window when available, and falls back to Firefox through
`app/window.py`.

## What It Shows

- Live hcom conversation and agent presence.
- MAP state and runtime health.
- Operator attention inbox for questions, approvals, and terminal prompts.
- Embedded ProjectUpdater at `/project-updater/`.
- Standalone ProjectUpdater launch/status actions.

ProjectUpdater itself lives in the MAP checkout at:

```text
Projects/ProjectUpdater/app/index.html
```

ProjectUpdater records remain browser-localStorage owned. CommandCenterUI reads
only the explicit status export at `~/Downloads/project-updater-status.json`.

## Entrypoints

- `run-command-center-app.sh` - full app window, or `--server-only`.
- `app/window.py` - GTK/WebKit wrapper with Firefox fallback.
- `app/server.py` - localhost backend.
- `src/chat.html`, `src/chat.js`, `src/chat.css` - main chat UI.
- `src/app.html` - older MAP dashboard view.
- `src/index.html`, `src/studio.html` - static prototype/reference views.
- `CommandCenterUI.desktop` - local desktop launcher metadata.

Runtime logs, injection audit logs, and relay-summary caches are generated under
`runtime/` after the app runs.

