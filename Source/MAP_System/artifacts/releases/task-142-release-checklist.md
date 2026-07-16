# Release Checklist: TASK-142

## Header

```
task_id:      TASK-142
released_by:  claude-lab-magi
release_date: 2026-07-04
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-142 acted on TASK-140/TASK-141's remaining recommendations, split with
codex-lab-veto (who took TASK-143, the mirror reconciliation gate) to avoid
duplicate work on the same broadcast:

- Added the Broadcast Coordinator Convention to `AGENTS.md` and cross-linked
  it from `notes/helper-agent-guide.md`, closing TASK-140 gap #5.
- Recorded DEC-027 in `shared/decisions.md`, answering the operator's direct
  question: Emergence/Insights needs no further building (already enforced
  via DEC-026), while Research stays specification-only by deliberate,
  revisitable decision rather than by neglect.
- Added a warning-baseline mechanism to `validate_events.py`
  (`warning_baseline.json`, `--fail-on-new`) so future event-shape warnings
  cannot hide inside the accepted 33-line legacy baseline, wired into
  `run_tests.sh`, closing TASK-140 gap #6.

One rework round: codex-lab-veto's first review caught a missing
`Applies-To` field on DEC-027 (`validate_decisions.py` failure) and a
missing `output_paths` registration for `shared/decisions.md` — both fixed
and reconfirmed in the rereview
(`MAP_System/artifacts/reviews/task142-rereview-veto.md`). Emergence
capture considered: the review round-trip itself (output-path/schema drift
caught only at review time, same class as TASK-141) is already tracked as
a known pattern via TASK-143's mirror gate; nothing new to capture here.

Full MAP suite passed 37/37 throughout.
