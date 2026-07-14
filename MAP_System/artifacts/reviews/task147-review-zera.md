# Review: TASK-147 Orchestration Entrypoint And Decomposer Contract

```
task_id:      TASK-147
reviewer:     claude-lab-zera
review_date:  2026-07-13
task_owner:   codex-lab-mozu
```

Reviewer (claude-lab-zera) != task owner (codex-lab-mozu). Independence check
passes.

## Verdict

```
APPROVED
```

Update 2026-07-13: owner (codex-lab-mozu) added the 3 missing rows to
`shared/subsystem-apis.md` (Allocator, Validators, Status) and resubmitted.
Re-verified below; all 4 acceptance criteria now PASS. Original
CHANGES_REQUESTED pass preserved below for the record.

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Defines one operator-intent entrypoint and when direct messages must be repackaged into a dispatch packet | PASS | `ORCHESTRATION_ENTRYPOINT_SYSTEM.md` names `scripts/intake_request.py` as the single entrypoint and its "Direct Message Policy" section lists the repackaging rule plus five explicit exceptions. |
| 2 | Decomposer spec defines subtasks, dependency edges, output paths, acceptance criteria, risk class, approval gates, routing lane, and rollback expectation | PASS | `map-decomposer-spec.md`'s "Required Output Fields" lists all eight (`subtasks`, `dependencies`, `output_paths`, `acceptance_criteria`, `risk_class`, `approval_gates`, `routing_lane`, `rollback_expectation`) plus `task_type`/`role`. |
| 3 | Subsystem API index documents allocator, git lock, task claim, event, validator, emergence, local-helper, and status APIs | PASS (fixed) | Original submission's table had 14 rows but omitted **allocator**, **validator**, and **status** rows. Owner added: `Allocator` → `scripts/map_task.py create --task-id auto`; `Validators` → `validate_task_mirrors.py`/`validate_events.py`/`validate_task_graph.py`/`promote_task.py`/`release_task.py`; `Status` → `agents/status.json`/`reconcile_agents.py`/`limit_watcher.py`. All 8 named categories now have an explicit row. |
| 4 | Focused tests or documented dry runs verify intake_request.py emits the new dispatch/decomposer fields | PASS | `tests/test_intake_request.py` (4 tests) asserts `decomposer_contract["required_fields"]`, routing lane, risk/approval classification, and CLI JSON output. All pass. |

## Files Reviewed

- `MAP_System/ORCHESTRATION_ENTRYPOINT_SYSTEM.md`
- `MAP_System/artifacts/planning/map-decomposer-spec.md`
- `MAP_System/shared/subsystem-apis.md`
- `MAP_System/scripts/intake_request.py`
- `MAP_System/tests/test_intake_request.py`
- `MAP_System/scripts/run_tests.sh`
- `MAP_System/tasks/TASK-147.json`

## Forbidden Changes Check

- PASS: no self-review; reviewer `claude-lab-zera` is not owner `codex-lab-mozu`.
- PASS: changed files match the task's declared `output_paths` exactly.
- PASS: no edits to TASK-148's claimed output paths (migration inventory/plan/smoke-check) — lanes stayed clean per the operator's broadcast-coordination split.

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/ORCHESTRATION_ENTRYPOINT_SYSTEM.md` | YES — declared output path |
| `MAP_System/artifacts/planning/map-decomposer-spec.md` | YES — declared output path |
| `MAP_System/shared/subsystem-apis.md` | YES — declared output path |
| `MAP_System/scripts/intake_request.py` | YES — declared output path |
| `MAP_System/tests/test_intake_request.py` | YES — declared output path |
| `MAP_System/scripts/run_tests.sh` | YES — declared output path (registers the new test) |

## Verification

Commands run:

```bash
bash MAP_System/scripts/run_tests.sh
python3 MAP_System/scripts/validate_task_mirrors.py
python3 MAP_System/scripts/validate_events.py --fail-on-new
python3 MAP_System/scripts/validate_shared_state.py
```

Results:

- Full suite: `SUMMARY pass=38 fail=0 total=38` (includes the new
  `test_intake_request.py` tests inside the suite run).
- Task mirror validation: pass.
- Event validation: `errors=0 new_warnings=0`.
- Shared-state validation: 20 files checked, 0 failures, 0 warnings
  (`subsystem-apis.md` HPOM header is present and current).

## Findings

| Severity | File | Section | Finding | Required action | Outcome |
|---|---|---|---|---|---|
| REQUIRED | `MAP_System/shared/subsystem-apis.md` | API table | Table omitted 3 of the 8 subsystem categories the task's own acceptance criterion #3 names by name: allocator, validator, status. | Add 3 rows: Allocator, Validators, Status. | FIXED — owner added all 3 rows 2026-07-13; re-verified via `validate_shared_state.py` (20 checked/0 failures/0 warnings) and `run_tests.sh` (pass=38 fail=0). |

No open BLOCKER or REQUIRED findings remain.

## Notes

This is a narrow, mechanical gap — the substance of Wave 1 (single entry
point, decomposer contract, dispatch packet fields, tests) is solid and all
4 acceptance criteria are otherwise met. Recommend codex-lab-mozu add the 3
rows and resubmit; no code or test changes needed, no re-run of `run_tests.sh`
required beyond confirming `validate_shared_state.py` still passes after the
edit (HPOM header `last_verified` should bump to the edit date).

Separately, cross-checked TASK-148 (migration rollout plan, submitted this
session) against TASK-147's output: no path overlap, no contradiction. The
migration plan's Step 1 assumes the single-entry-point contract from
`ORCHESTRATION_ENTRYPOINT_SYSTEM.md` exists before Waves 4/5/8 gate dispatch
on it — that dependency holds once this finding is fixed.
