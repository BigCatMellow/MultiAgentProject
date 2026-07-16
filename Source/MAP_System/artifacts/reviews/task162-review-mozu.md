task_id: TASK-162
reviewer: codex-lab-mozu
task_owner: command-center
review_date: 2026-07-14

## Verdict

CHANGES_REQUESTED

## Findings

1. REQUIRED: `validate_protocol.py` cannot validate hcom `--intent` presence, so it cannot satisfy the protocol spec or the protocol halt probe.

   Evidence: `MAP_System/artifacts/planning/map-protocol-validator-spec.md` lists the first protocol scope check as "Does the message carry a required `--intent`?" `MAP_System/artifacts/tests/map-validator-halt-probe.md` defines the future Protocol halt test as a malformed hcom message "missing required `--intent` on a broadcast request." TASK-162's description also says to wire protocol-validator checks for "hcom intent presence".

   The implementation only accepts message text plus `--operator-decision-request`:

   - CLI: `validate_protocol.py TEXT [--operator-decision-request] [--json]`
   - API: `evaluate_protocol(text, is_operator_decision_request=False)`

   There is no `intent`/`has_intent` input, no check for absent/invalid intent, and no test covering the missing-intent probe. A message can therefore pass protocol validation even when the hcom metadata omitted the required intent, because the validator cannot observe that condition.

   Required fix: add an explicit intent input/check to the protocol validator API and CLI, preserve text-only behavior only when intent validation is intentionally not applicable, and add focused tests proving missing/invalid intent fails while valid `inform`/`request`/`ack` style intents pass. The default DRIFT cap should still prevent halt-store writes unless severity is explicitly raised.

## Acceptance Criteria Check

| # | Result | Evidence |
|---|---|---|
| 1 | PASS | `validate_layer1.py` composes existing validators via subprocess calls and reports per-validator breakdown; structural test confirms no schema/table creation. |
| 2 | PARTIAL | MATOCP token-shape and adjudication default are implemented, but the protocol validator omits hcom intent presence despite the spec/task requiring it. |
| 3 | PASS | Both validators use TASK-159 `halt_state.set_halt()` for escalated BLOCKING/STRUCTURAL findings, and tests assert no second halt table. |
| 4 | PASS | Default `DRIFT` severity does not write halt state; tests prove telemetry-only default behavior. |
| 5 | FAIL | The "Protocol halt test" probe cannot pass because the validator cannot detect missing `--intent`; semantic/L1 halt-store integration is present. |

## Verification Run

- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_validate_protocol.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_validate_layer1.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/scripts/validate_layer1.py --json`
- PASS: `MAP_System/.venv/bin/python MAP_System/scripts/validate_protocol.py "!REQ TASK-1 please decide" --json`
- INSPECTED: `map-protocol-validator-spec.md`, `map-semantic-validator-spec.md`, `map-validator-halt-state-spec.md`, and `map-validator-halt-probe.md`.

## Notes

I did not edit TASK-162 implementation files. This review only adds `MAP_System/artifacts/reviews/task162-review-mozu.md`.
