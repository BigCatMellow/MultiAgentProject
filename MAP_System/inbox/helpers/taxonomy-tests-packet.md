# Work Packet: Close Taxonomy-Audit Regression Tests #4–#6

Intended implementer: claude-lab-toku (after TASK-187 review + TASK-188 release)
Dispatcher: claude-lab-mira (lead)
Source: `artifacts/audits/source-mining-audit-2026-07-14.md` ranked item #5;
origin `artifacts/audits/map-failure-taxonomy-coverage.md` (its own #4/#5/#6,
named highest-value missing tests; #7 stays gated on the write-control decision)

## Goal

Three focused test files closing the taxonomy audit's named coverage holes.
Read the taxonomy audit's descriptions first — they define the failure modes;
this packet only fixes scope.

## Scope

1. `tests/test_decomposer_edges.py` (taxonomy #4): dependency-edge cases in
   task decomposition/graph validation — cycles beyond the trivial 2-node case,
   self-dependency, dangling dependency IDs, diamond dependencies with mixed
   terminal/active states. Exercise `validate_task_graph.py` (and
   `graph/runner.py`'s ready-computation if reachable as pure functions).
2. `tests/test_context_summary_drift.py` (taxonomy #5): context-summary drift —
   a summary/mirror that no longer matches its source must be detectable.
   Anchor on what exists: `validate_shared_state.py` metadata staleness,
   `validate_task_mirrors.py` drift detection. Test the detectors' negative
   paths (drift present → detector fires), not just happy paths.
3. `tests/test_multi_project_isolation.py` (taxonomy #6): multi-project
   isolation — Pathwell/ProjectUpdater-class project state must not leak into
   MAP_System decisions. Anchor on `map-multi-project-readiness.md`'s stated
   boundaries; test that the runner/task tooling scoped to MAP_System ignores
   or rejects records claiming other project_ids where isolation is promised.
4. Wire all three into `run_tests.sh`.

## Rules

- Where a taxonomy hole has NO detector to test (i.e. the isolation promise
  exists only in prose), write the test that SHOULD pass, mark it skipped with
  a reason string naming the missing mechanism, and list it in your report —
  a skipped-with-reason test is an honest tracked gap; a fabricated pass is not.
- Task record via --task-id auto (announce ID). Output paths: the three test
  files + run_tests.sh + a short report in artifacts/tests/.
- Report: files, pass/skip counts per file, suite total, and any real bugs the
  new tests flush out (file repairs via map_repair.py if BLOCKING/DRIFT).
