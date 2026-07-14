task_id: TASK-161
reviewer: codex-lab-mozu
task_owner: command-center
review_date: 2026-07-14

## Verdict

APPROVED

## Prior Finding Check

| Prior finding | Result | Evidence |
|---|---|---|
| `durable_execution.record_checkpoint()` allowed backward step regression, e.g. `claim -> handler -> claim`, causing resume to replay an already-completed boundary. | FIXED | `record_checkpoint()` now enforces monotonic `STEP_ORDER` progression and rejects any step whose index is less than or equal to the latest recorded step. `test_recording_an_earlier_step_after_a_later_one_is_rejected()` covers the prior repro. An independent isolated probe confirmed `claim -> handler -> claim` now raises `DurableExecutionError`. |
| `resilience_controls.check_and_record()` allowed same idempotency key with different request content while the prior record was still `started`. | FIXED | `check_and_record()` now compares hashes for both `started` and `applied` records. It raises `IdempotencyConflict` for started+different payload and returns the existing in-progress record for started+same payload. Focused tests cover both paths, and an independent isolated probe confirmed the old two-started-records case now raises. |

## Acceptance Criteria Check

| # | Result | Evidence |
|---|---|---|
| 1 | PASS | Idempotency registry covers started/applied duplicate handling, started/applied conflict handling, failed retry behavior, and dead-letter enqueue/replay/depth validation. |
| 2 | PASS | Durable checkpoint/resume helpers cover claim/handler/submit/event/export order, duplicate and backward-step rejection, killed-handler resume, and independent task checkpoint state. |
| 3 | PASS | Circuit-breaker escalation uses TASK-159 `halt_state.set_halt()` for scoped repair/global halt behavior; tests assert no second halt table. |
| 4 | PASS | Six executable chaos probes cover killed handler, stale mirror, malformed protocol output, hung agent/reaper path, mid-task resume, and committed poisoned-state recovery, all against isolated fixtures/temp logs. |

## Verification Run

- PASS: independent backward checkpoint repro now raises `DurableExecutionError`.
- PASS: independent started-idempotency hash mismatch repro now raises `IdempotencyConflict`.
- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_durable_execution.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_resilience_controls.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_chaos_resilience.py`
- PASS: `python3 -m py_compile MAP_System/scripts/dead_letter_queue.py MAP_System/scripts/durable_execution.py MAP_System/scripts/resilience_controls.py MAP_System/tests/test_durable_execution.py MAP_System/tests/test_resilience_controls.py MAP_System/tests/test_chaos_resilience.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/scripts/validate_task_mirrors.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py --fail-on-new` (`errors=0`, `new_warnings=0`, legacy warnings only)
- PASS: `MAP_System/scripts/run_tests.sh` (`SUMMARY pass=50 fail=0 total=50`)

## Files Reviewed

- `AGENTS.md`
- `MAP_System/AGENTS.md`
- `MAP_System/tasks/TASK-161.json`
- `MAP_System/artifacts/planning/map-resilience-controls-spec.md`
- `MAP_System/artifacts/planning/map-durable-execution-spec.md`
- `MAP_System/artifacts/tests/map-chaos-test-plan.md`
- `MAP_System/artifacts/reviews/task161-review-mozu.md`
- `MAP_System/scripts/dead_letter_queue.py`
- `MAP_System/scripts/durable_execution.py`
- `MAP_System/scripts/resilience_controls.py`
- `MAP_System/tests/test_durable_execution.py`
- `MAP_System/tests/test_resilience_controls.py`
- `MAP_System/tests/test_chaos_resilience.py`
- `MAP_System/scripts/validate_review.py`

## Forbidden Changes Check

- PASS: reviewer is independent from the task implementer.
- PASS: this rereview only adds `MAP_System/artifacts/reviews/task161-rereview-mozu.md`.
- PASS: I did not edit TASK-161 implementation/test files.
- PASS: security second-pass is not required; TASK-161 is local resilience/durable-state tooling and the reviewed risks were durable state correctness plus shared halt-store reuse.

## Findings

No blocking findings remain.
