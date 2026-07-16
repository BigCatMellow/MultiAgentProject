# Release Checklist: TASK-091

## Header

```text
task_id:      TASK-091
released_by:  codex-lab-lema
release_date: 2026-07-02
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared

## Summary

TASK-091 is ready to release: CommandCenterUI now has a global hidden-attribute
CSS guard so the agent screen panel, lab banner, and mention hint stay hidden
whenever the `hidden` attribute is set, even when component classes define
their own display values.
