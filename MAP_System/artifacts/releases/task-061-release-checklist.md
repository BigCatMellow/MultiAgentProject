# Release Checklist: TASK-061

## Header

```
task_id:      TASK-061
released_by:  codex-lab-maki
release_date: 2026-07-01
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared

## Summary

TASK-061 resolved the REQUIRED stale-artifact finding from TASK-059. The
published Dark_Mellow GitHub repository no longer exposes
`Mellow-Dark-theme-2026-06-30.zip`, `README.txt` now points users to the current
wallpaper-aware installer path, and `README.md` no longer tells users that old
ad hoc ZIP uploads are retained. The stale ZIP was preserved locally under
`Projects/DarkMellow/artifacts/retired/` for auditability.

The fix was pushed to `BigCatMellow/Dark_Mellow` as commit `9b9a9f0`
(`Remove stale theme ZIP`) and approved by `claude-lab-taro` after live GitHub
verification.
