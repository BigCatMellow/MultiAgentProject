task_id: TASK-161
reviewer: codex-lab-mozu
task_owner: command-center
review_date: 2026-07-14

## Verdict

CHANGES_REQUESTED

## Findings

1. REQUIRED: `durable_execution.record_checkpoint()` allows backward step regression, which can double-apply completed write boundaries.

   Evidence: `record_checkpoint()` only rejects the same step when it is repeated immediately (`last["step"] == step`). It does not reject an earlier step after a later one. In an isolated probe, I recorded `claim`, then `handler`, then `claim` again; the helper accepted all three records and `resume_step()` returned `handler` again. That means a resumed process can regress from a later completed boundary back to an already-completed earlier boundary, directly violating the durable execution spec's requirement to resume at the first incomplete step and avoid replaying completed writes.

   Required fix: enforce monotonic step order for a task's checkpoint sequence. Recording a step whose `STEP_ORDER` index is less than or equal to the latest recorded step should fail unless an explicit, safe new execution/attempt boundary is represented. Add a regression test that `claim -> handler -> claim` is rejected.

2. REQUIRED: `resilience_controls.check_and_record()` allows the same idempotency key to be reused with different request content while the prior record is still `started`.

   Evidence: the spec says "If the same key has a different request hash, stop with `conflict`" and "Never reuse a key for different semantic content." The implementation only checks different request hashes when the latest record is `applied`; for a latest `started` record it appends another `started` record with the same key and different `request_hash`. My isolated probe produced two `started` records for key `K` with different hashes and no `IdempotencyConflict`.

   Required fix: compare request hashes for any existing record for the key, not only `applied` records. Different hash must raise/record conflict; same hash with `started` should be handled as an in-progress duplicate according to the checkpoint/resume policy rather than silently appending a fresh `started` intent. Add focused tests for started+different payload and started+same payload behavior.

## Acceptance Criteria Check

| # | Result | Evidence |
|---|---|---|
| 1 | FAIL | Duplicate-after-applied and conflict-after-applied are tested, but started-state conflicting reuse is currently accepted, so the idempotency registry does not fully implement duplicate/conflict behavior. Dead-letter replay vocabulary is present. |
| 2 | FAIL | Checkpoint records and resume helpers exist, but backward step regression allows replaying already-completed boundaries. |
| 3 | PASS | Circuit-breaker escalation uses TASK-159 `halt_state.set_halt()` for repair/global states, and tests assert no second halt table. |
| 4 | PARTIAL | The six named chaos probes exist and pass in isolated fixtures, but their current coverage misses the checkpoint regression and started-idempotency conflict cases above. |

## Verification Run

- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_durable_execution.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_resilience_controls.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_chaos_resilience.py`
- REPRO: isolated `record_checkpoint('claim')`, `record_checkpoint('handler')`, `record_checkpoint('claim')` was accepted and made `resume_step()` return `handler` again.
- REPRO: isolated `check_and_record('K', payload1)` followed by `check_and_record('K', payload2)` appended two `started` records with different request hashes and no conflict.

## Files Reviewed

- `AGENTS.md`
- `MAP_System/AGENTS.md`
- `MAP_System/tasks/TASK-161.json`
- `MAP_System/artifacts/planning/map-resilience-controls-spec.md`
- `MAP_System/artifacts/planning/map-durable-execution-spec.md`
- `MAP_System/artifacts/tests/map-chaos-test-plan.md`
- `MAP_System/scripts/dead_letter_queue.py`
- `MAP_System/scripts/durable_execution.py`
- `MAP_System/scripts/resilience_controls.py`
- `MAP_System/tests/test_durable_execution.py`
- `MAP_System/tests/test_resilience_controls.py`
- `MAP_System/tests/test_chaos_resilience.py`
- `MAP_System/scripts/validate_review.py`

## Forbidden Changes Check

- PASS: reviewer is independent from the task implementer.
- PASS: this review only adds `MAP_System/artifacts/reviews/task161-review-mozu.md`.
- PASS: I did not edit TASK-161 implementation/test files.
- PASS: security second-pass is not required for this local resilience-control implementation; the reviewed risks are durable state correctness and shared halt-store reuse.
