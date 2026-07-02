# Release Checklist: TASK-089

## Header

```text
task_id:      TASK-089
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

- `run-command-center-app.sh` continues to open the app window.
- The app window calls the local backend, which exposes lab status/start and terminal screen APIs.
- Live `127.0.0.1:8765` endpoints were checked for lab status, term read, malformed input, same-origin guard, and readonly hcom DB behavior.

No archive, installer, or remote package is part of this task.

## Summary

TASK-089 is ready to release: CommandCenterUI now acts as the all-in-one lab
front-end, can start or revive the lab path through existing visible launchers,
shows agent terminal screens, and provides guarded/audited prompt injection.
