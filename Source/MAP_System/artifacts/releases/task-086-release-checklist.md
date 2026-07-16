# Release Checklist: TASK-086

## Header

```text
task_id:      TASK-086
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

- README run command points at `/home/home/Projects/CommandCenterUI/run-command-center-app.sh`.
- `CommandCenterUI.desktop` Exec points at `/home/home/Projects/CommandCenterUI/run-command-center-app.sh`.
- `run-command-center-app.sh` and `launch-command-center-ui.sh` pass `bash -n`.
- The app served live MAP data from `http://127.0.0.1:8876/` during review.

No release archive, remote package, or installer is part of this task. The
remaining noted follow-ups are cosmetic only: static prototype text still has
old decorative path copy, and `desktop-file-validate` reports a non-failing
multi-category hint.

## Summary

TASK-086 is ready to release: CommandCenterUI now runs as a standalone local
app from `/home/home/Projects/CommandCenterUI`, resolves the live
MultiAgentProject workspace, exposes non-empty MAP state through the local API,
and keeps the existing guarded hcom-send behavior.
