# Release Checklist: TASK-087

## Header

```text
task_id:      TASK-087
released_by:  codex-lab-lema
release_date: 2026-07-02
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared

## Release-Path Smoke

Acquisition paths checked:

- `/home/home/Projects/CommandCenterUI/run-command-center-app.sh` launches the native wrapper path by default.
- `/home/home/Projects/CommandCenterUI/run-command-center-app.sh --server-only` preserves backend-only mode.
- `CommandCenterUI.desktop` points at the current launcher and validates.
- Live app at `http://127.0.0.1:8765/` serves `chat.html`; old dashboard remains at `/app.html`.
- `/api/chat`, `/api/presence`, `/api/tasks`, `/chat.js`, and `/chat.css` return live data/assets.

No archive, installer, or remote package is part of this task.

## Summary

TASK-087 is ready to release: CommandCenterUI now opens as its own app window,
uses a chatroom-first UI with live hcom feed/presence, supports one-box
operator sends through external `command-center` attribution, and keeps MAP
state as a secondary dashboard.
