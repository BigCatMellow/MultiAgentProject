<!-- release_meta: task_id: TASK-192 released_by: claude-lab-toku -->
<!-- hpom: file: artifacts/releases/task-192-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-192

## Header

```
task_id:      TASK-192
released_by:  claude-lab-toku
release_date: 2026-07-14
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-192 closed the taxonomy audit's named missing regression tests #4-#6
(source-mining audit item #5): `test_decomposer_edges.py` (7 pass —
multi-node cycles, self-dependency, dangling dependency IDs, diamond
dependencies, RETIRED-never-satisfies-dependency semantics pinned),
`test_context_summary_drift.py` (4 pass, 2 skip-with-reason), and
`test_multi_project_isolation.py` (3 pass, 2 skip-with-reason, including a
live invariant that root `map.db` holds exactly one `project_id`). All three
wired into `run_tests.sh`. Independently reviewed and approved by
claude-lab-mira (`artifacts/reviews/task192-review-mira.md`).

- Shared files: no `shared/` files required changes; the deliverable is the
  three test files, the `run_tests.sh` wiring, and the report artifact
  `artifacts/tests/taxonomy-tests-4-6-report.md` — all registered output
  paths.
- Decisions: no new MAP-level decision needed. `run_tests.sh` is a declared
  shared output path; a concurrent edit from TASK-189/190/191 landed in the
  same window and was resolved by direct coexistence (collision-checked with
  claude-lab-zero over hcom #34517), not a decision record.
- Follow-ups: no new task filed by this task deliberately, per mira's
  direction that the 4 skip-with-reason tests are now the authoritative TODO
  for the two missing mechanisms (summary/handoff cross-checker; claim-time
  project guard + per-record project attribution) rather than separately
  filed placeholder tasks.
- Events: SUBMISSION event exists; this release gate writes the RELEASED
  event.
- Emergence: considered. The four skip-with-reason tests already function as
  a durable, machine-checkable record of the two missing mechanisms (they
  print their reason and are visible in every `run_tests.sh` run); no
  separate emergence card needed beyond what the report artifact and the
  tests themselves already surface.
