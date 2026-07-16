<!-- hpom: file: artifacts/releases/task-197-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-197

## Header

```
task_id:      TASK-197
released_by:  codex-lab-nivo
release_date: 2026-07-15
implemented_by: codex-lab-mozu
reviewed_by:    claude-lab-mira
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-197 adds a report-only decision-conflict pass to
`validate_decisions.py`. It detects one-way or dangling supersession metadata
and conservative same-subject decision pairs lacking an explicit supersession
relationship. The first pass intentionally does not gate validation failures.

- Shared files: `MAP_System/scripts/validate_decisions.py`,
  `MAP_System/tests/test_decision_conflicts.py`,
  `MAP_System/scripts/run_tests.sh`, and
  `MAP_System/artifacts/tests/task197-decision-conflict-run.md`.
- Decisions: no policy decision changed. `MAP_System/shared/decisions.md` was
  not edited to hide findings.
- Follow-ups: no standalone task required. The three reciprocal-supersession
  cleanup notes for `DEC-004`, `DEC-007`, and `DEC-012` should be folded into
  the next normal `decisions.md` touch.
- Events: approval and release are recorded in `events/events.jsonl`.
- Emergence: considered. This closes the last agent-startable item from the
  source-mining audit; no additional emergence artifact is needed.

## Verification

- `MAP_System/tests/test_decision_conflicts.py`: 3/3 pass in review.
- `MAP_System/scripts/validate_decisions.py`: pass in review with 27 decisions
  checked, 0 hard failures, and 3 report-only one-way supersession notes.
- `MAP_System/scripts/run_tests.sh`: 65/65 pass in review.
- Independent review: `artifacts/reviews/task197-review-mira.md`.
