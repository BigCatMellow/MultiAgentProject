<!-- hpom: file: artifacts/tests/taxonomy-tests-4-6-report.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: TASK-192 test run -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# TASK-192 Report: Taxonomy-Audit Regression Tests #4-#6

- Task: TASK-192 (owner claude-lab-toku)
- Origin: `artifacts/audits/map-failure-taxonomy-coverage.md` missing tests
  #4/#5/#6; ranked item #5 in `artifacts/audits/source-mining-audit-2026-07-14.md`
- Packet: `inbox/helpers/taxonomy-tests-packet.md`

## Files

| File | Pass | Skip | Wired into run_tests.sh as |
|---|---|---|---|
| `tests/test_decomposer_edges.py` | 7 | 0 | `decomposer_edges_test` (venv python — imports `graph/runner.py`) |
| `tests/test_context_summary_drift.py` | 4 | 2 | `context_summary_drift_test` |
| `tests/test_multi_project_isolation.py` | 3 | 2 | `multi_project_isolation_test` |

Skips are deliberate skipped-with-reason tests per the packet rule: each
prints the missing mechanism it is waiting for and carries the intended
assertion in its docstring — an honest tracked gap, not a fabricated pass.

## Taxonomy #4 — decomposer/dependency edges (7 pass)

Against `validate_task_graph.validate()` (run with module ROOT pointed at a
tmpdir of matching task-file stubs, so synthetic graphs don't trip the
task-file-existence check) and `graph/runner.evaluate_tasks()`:

- 3-node cycle (A→C→B→A) detected; self-dependency detected as a cycle.
- Dangling dependency ID reported as `unknown dependency` and NOT
  misreported as a cycle (the validator's skip-unknown branch).
- Diamond (D terminal ← B ready, C in-progress ← A) validates clean.
- Runner ready-computation on the same diamond: B ready, A blocked
  (waits on active B/C), C in-progress.
- **RETIRED dependency does not satisfy** (TASK-100 semantics pinned):
  `DEPENDENCY_SATISFIED_STATUSES` excludes RETIRED and a READY task
  depending on a RETIRED one stays blocked.
- Self-depending READY task is never dispatched ready.

## Taxonomy #5 — context/summary drift (4 pass, 2 skip)

Negative paths of the existing detectors (drift injected → detector fires):

- Task present in canonical SQLite but missing from the task-graph summary
  mirror → `validate_task_mirrors` fires (`task_graph.json missing ...`).
- Ghost mirror file with no canonical row behind it → fires
  (`task file mirror has no SQLite task`).
- `validate_shared_state.check_file`: STALE / SUPERSEDED / NEEDS_REVIEW
  statuses each flagged; clean CURRENT header produces zero issues;
  missing header and missing required fields (e.g. `last_verified`) flagged.

Skipped-with-reason (missing mechanisms):

1. `test_summary_content_drift_detector_missing` — no content-drift
   detector exists: `validate_shared_state.py` reads only the self-declared
   hpom header; nothing compares summary content (or checksum/mtime linkage)
   against the source it summarizes.
2. `test_handoff_missing_blocker_detector_missing` — taxonomy #5's named
   case ("compressed handoff missing blocker") has no detector:
   `validate_context_packets.py` checks template fragments and placeholders
   only; packet/handoff claims are never cross-referenced against canonical
   task state.

## Taxonomy #6 — multi-project isolation (3 pass, 2 skip)

Anchored on `map-multi-project-readiness.md`'s boundaries:

- **Live invariant on real state**: root `map.db` contains exactly one
  `project_id` and `workflow/task_graph.json` declares the same one — a
  Pathwell/ProjectUpdater record leaking into root MAP state now fails the
  suite.
- `map_task.project_id()` derives from the database being written, so task
  creation cannot silently attach to a foreign project.
- Claims are scoped to the explicit `db_path`: claiming in a project-local
  fixture DB succeeds there and leaves root map.db untouched.

Skipped-with-reason (missing mechanisms):

1. `test_cross_project_claim_guard_missing` — `db/claims.py` never consults
   `project_id` at claim time; isolation rests on physically separate
   per-project database files, which is a prose rule
   (map-multi-project-readiness.md), not a gate.
2. `test_mirror_records_carry_no_project_attribution` — task JSON mirrors
   and graph entries carry no per-record `project_id`, so a foreign
   project's record copied into root mirrors is indistinguishable by every
   current validator.

## Bugs flushed out

None BLOCKING/DRIFT — no `map_repair.py` record needed. Two fixture-level
findings worth noting (not defects): `tasks.owner` has a FOREIGN KEY to
`agents`, and the claim gate refuses tasks without non-empty acceptance
criteria and output paths — both bit the first fixture drafts and are now
encoded in the fixtures, which doubles as documentation of the claim gate's
actual requirements.

## Suite state

- All three files green standalone (see per-file counts above; skips exit 0
  by design and print their reasons into the suite log).
- Wired into `run_tests.sh` (lines adjacent to the integration checks;
  `decomposer_edges_test` uses `.venv/bin/python` like the other
  runner-importing tests).
- run_tests.sh was concurrently extended by TASK-189/190/191 owners
  (outcome_feedback_test, cost_yield_test, redaction_test) — both edits
  coexist (collision checked with claude-lab-zero over hcom, hcom #34517;
  run_tests.sh is a declared shared output path). Full-suite total at
  submission time is recorded below.
- Full suite at submission: `run_tests.sh` SUMMARY pass=61 fail=0 total=61.
  An earlier merged run showed pass=60 fail=1 while TASK-189/190/191 were
  still landing concurrently; that failure belonged to their in-flight work,
  not TASK-192, and cleared once they finished — all three TASK-192 checks
  passed in both runs.

## Missing-mechanism follow-up candidates (for the lead, not filed here)

The four skips map to two concrete mechanism gaps if the lead wants them
closed: (a) a summary/handoff cross-checker (content or claim vs canonical
state) covering both #5 skips; (b) claim-time project guard + per-record
project attribution covering both #6 skips.
