# Release Checklist: TASK-126

## Header

```text
task_id:      TASK-126
released_by:  claude-lab-valo
release_date: 2026-07-03
review_record: MAP_System/artifacts/reviews/task126-review-dino.md
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

Operator-directed (POLICY-class) task: backfilled real Emergence records
for ProjectUpdater (INS-0011, INS-0012, INS-0013, IDEA-0015 — triaged, not
left RAW) after the operator identified that the Emergence/Insight system
was never used during that project's build despite applying. Made
Emergence capture mandatory for every project going forward:

- `PROJECT_BOOTSTRAPPING_SYSTEM.md` and `NEW_PROJECT_WIZARD.md` now
  require Emergence folders at bootstrap and per-task consideration.
- `CHANGE_CONTROL_SYSTEM.md` and `scripts/release_task.py` mechanically
  require an "Emergence capture considered" checklist line — this very
  checklist is the first release to go through that new gate.
- `templates/release-checklist.md` and `tests/test_release_gate.py`
  updated to match, with a new passing test proving the gate blocks a
  checklist missing the line.
- Recorded as DEC-026.

Reviewed by codex-lab-dino: APPROVED, no BLOCKER/REQUIRED findings. His
note that `Projects/ProjectUpdater/{insights,ideas,experiments,synthesis}/`
are capacity/README stubs (since `map_emergence.py` stores real records
centrally under `MAP_System/emergence/` with `Project:` metadata, not in
project-local folders) is accurate and already documented in each stub's
README.

## Verification

```text
validate_shared_state.py: 19 checked, 0 failures, 0 warnings
validate_decisions.py: 26 decisions checked, 0 failures
validate_task_graph.py: PASS
map_emergence.py validate: OK, 35 artifacts checked
map_emergence.py stale: no findings
test_exporter_invariants.py: PASS
test_release_gate.py: PASS (4 tests, including new
  test_missing_emergence_line_blocks_release)
full MAP suite (scripts/run_tests.sh): pass=33 fail=0 total=33
runner route before approval: review (no-self-review honored; dino reviewed)
```
