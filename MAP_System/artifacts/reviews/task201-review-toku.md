<!-- hpom: file: artifacts/reviews/task201-review-toku.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: TASK-201 submitted diff + local verification -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Review Record: TASK-201

## Header

```
task_id:      TASK-201
reviewer:     claude-lab-toku
review_date:  2026-07-15
task_owner:   codex-lab-nivo
```

Reviewer (claude-lab-toku) ≠ task owner (codex-lab-nivo). Independence check
passes. Review claimed via `claim_review("TASK-201", "claude-lab-toku")`
before starting, per nivo's request.

---

## Verdict

```
APPROVED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Window inactive or expired preserves current telemetry-only validator behavior | PASS | `halt_authority_window_status()` fails safe: missing config, null `enabled_until`, past timestamp, invalid timestamp, or scope mismatch all return `active: False`. `maybe_set_halt()` in both validators only escalates `DRIFT` → `BLOCKING` when `window["active"]` is true; both live CLI entrypoints call `maybe_set_halt` with the existing `DEFAULT_SEVERITY_CAP="DRIFT"`, so an inactive window reproduces exactly the pre-TASK-201 `return None` path. `test_disabled_window_is_inactive` and `test_inactive_window_preserves_telemetry_only_and_logs_would_halt` (halt_id is None, no halt file written) confirm this; reproduced independently. |
| 2 | Active window scoped to layer1/protocol writes an operator-clearable halt through `halt_state.py` when a validator violation fires | PASS | Active window escalates `DRIFT`→`BLOCKING`, which then reaches the pre-existing `set_halt(...)` call with `clear_requires="operator" if window["active"] else "command_center"`. `test_active_layer1_window_writes_operator_clearable_halt` and `test_active_protocol_window_writes_halt_for_protocol_violation` both assert `record["clear_requires"] == "operator"`; reproduced independently. |
| 3 | Scope filtering prevents unrelated validators from halting | PASS | `halt_authority_window_status(validator_scope, ...)` checks `"*" not in scopes and scope not in scopes` → `scope_mismatch`, inactive. `test_expired_or_scope_mismatched_windows_do_not_halt` covers a `scope: [protocol]`-only window queried by the `layer1` validator scope — correctly inactive. |
| 4 | Halt-or-would-halt decisions are logged with adjudication status pending | PASS | `append_validator_halt_event()` always writes `"adjudication": "pending"` in the summary JSON for both `decision: "would_halt"` (inactive/DRIFT path) and `decision: "halt_set"` (active path). All three positive-path tests assert `summary["adjudication"] == "pending"`; reproduced independently. |
| 5 | Mechanism ships disabled; operator enablement is documented as a one-line action | PASS | `runtime_policy.yaml`'s new block ships `enabled_until: null, granted_by: null, scope: []` — inactive by every code path. `notes/halt-authority-window-runbook.md` documents the enable/disable edit as a single YAML block change, with `scope` combinations explained. |
| 6 | Focused tests and relevant suite checks pass | PASS | Reproduced independently: `test_halt_authority_window.py` 5/5; `validate_task_mirrors.py`, `validate_task_graph.py` pass; `validate_events.py --fail-on-new` errors=0 new_warnings=0; full `run_tests.sh` pass=67 fail=0 total=67 (includes the new `halt_authority_window_test` line in `run_tests.sh`). |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Enabling the window (packet: "Do NOT enable the window. Shipping the mechanism disabled IS the task.") | NOT BROKEN — `enabled_until: null` in the shipped `runtime_policy.yaml`; confirmed inactive by direct test |
| Adding a second halt table / bypassing `halt_state.py`'s existing store | NOT BROKEN — both validators' docstrings and code still route through the single `set_halt()` call; no new halt storage introduced |
| Weakening the STRUCTURAL/BLOCKING-severity halt path that already existed independent of the window | NOT BROKEN — `effective_severity` only ever escalates DRIFT upward when the window is active; explicit BLOCKING/STRUCTURAL findings are untouched by the window logic (the `if effective_severity == "DRIFT": ... return None` branch is unreachable for them either way) |

---

## Files Reviewed

- `MAP_System/workflow/runtime_policy.yaml` (+4 lines: disabled-by-default block)
- `MAP_System/scripts/halt_state.py` (+~130 lines: `halt_authority_window_status`, `load_runtime_policy`, `append_validator_halt_event`, helpers)
- `MAP_System/scripts/validate_layer1.py` (window wiring into `maybe_set_halt`, new CLI flags)
- `MAP_System/scripts/validate_protocol.py` (symmetric window wiring)
- `MAP_System/tests/test_halt_authority_window.py` (new, 5 tests)
- `MAP_System/notes/halt-authority-window-runbook.md` (new)
- `MAP_System/scripts/run_tests.sh` (+1 line)

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/workflow/runtime_policy.yaml` | YES — declared output path |
| `MAP_System/scripts/halt_state.py` | YES — declared output path |
| `MAP_System/scripts/validate_layer1.py` | YES — declared output path |
| `MAP_System/scripts/validate_protocol.py` | YES — declared output path |
| `MAP_System/tests/test_halt_authority_window.py` | YES — declared output path |
| `MAP_System/notes/halt-authority-window-runbook.md` | YES — declared output path |
| `MAP_System/scripts/run_tests.sh` | YES — declared output path; single added line, no conflict with concurrent edits from other Wave 3 lanes |

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| `halt_authority_window_status` reads `runtime_policy.yaml` fresh on every validator invocation (no caching) — fine for CLI-per-run usage, but would add file I/O per call if a future caller invokes validators in a tight loop | LOW | No action needed at current usage patterns (one-shot CLI invocations); note for whoever eventually builds the continuous validator loop from the master plan |
| `VALID_HALT_AUTHORITY_SCOPES = {"layer1", "protocol", "*"}` is a closed set; a typo'd scope in `runtime_policy.yaml` (e.g. `"Layer1"`) is lowercased by `_normalize_window_scopes` before comparison, so casing typos are forgiving, but a genuinely wrong scope name silently fails to activate rather than erroring | LOW | Acceptable — fail-safe-inactive is the correct default for a typo; the runbook's copy-pasteable YAML block minimizes the chance of a typo in practice |

---

## Findings

No BLOCKER or REQUIRED findings.

---

## Notes

- Verification fully reproduced independently, not taken from the
  submission: focused tests 5/5, both structural gates, event-shape gate
  (new_warnings=0), and full suite 67/67.
- The design cleanly reuses the existing single-halt-store architecture
  (TASK-159/162) rather than introducing parallel state — the window only
  ever changes which severity a validator computes before reaching the
  pre-existing `set_halt()` call, which is the right shape for "extend an
  existing mechanism" rather than "add a new one."
- This closes re-grade trigger #2 from `map-robustness-grading-2026-07-14.md`
  operationally: the C1 (eager halt) and V (L2 false-positive target)
  conclusions can now actually be measured against a real bounded window
  once the operator chooses to run one, without any further code work.
