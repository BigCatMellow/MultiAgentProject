# Release Checklist: TASK-101

## Header

```text
task_id:      TASK-101
released_by:  codex-lab-lema
release_date: 2026-07-02
review_record: MAP_System/artifacts/reviews/task101-review-limo.md
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared

## Summary

TASK-101 is ready to release: source/mirror drift is now covered by focused
export invariants for task status propagation and the filtered operational
agent-status view. `run_tests.sh` is explicitly treated as a narrow shared test
suite registry, with a regression test confirming ordinary duplicate output
paths still fail.

No new durable decision was needed; this implements the source/mirror drift
hardening identified by the TASK-099 effectiveness review. No follow-up tasks
are required.

Release note: `codex-lab-lema` completed the actual `map_task.py release`.
`codex-lab-limo` attempted the same release seconds later and the release gate
correctly rejected it because TASK-101 was already `RELEASED`.

## Verification

```text
exporter invariants: PASS
shared output path regression: PASS
task graph: passed
full MAP suite: pass=25 fail=0 total=25
review record validation: passed
runner route before release: wait_or_reconcile
```
