# Review: TASK-164 Harden Read-Only Mission-Control Attention Surfaces

```
task_id:      TASK-164
reviewer:     claude-lab-zera
review_date:  2026-07-14
task_owner:   codex-lab-mozu
```

Reviewer (claude-lab-zera) != task owner (codex-lab-mozu). Independence
check passes. (I built the original mission-control-tui.py/_mission_control_app.py
under TASK-160, but this is a distinct follow-on task with a different
owner, and I did not write TASK-164's changes.)

## Verdict

```
APPROVED
```

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Policy-gated and policy-rejected tasks from runner snapshots are visible in flight-board data and attention items | PASS | `get_flight_board()` adds `policy_gated`/`policy_rejected` keys read from `graph/runner.py`'s existing `policy_gated_tasks`/`policy_rejected_tasks` fields (confirmed these fields exist in real runner output). `get_attention_queue()` adds `policy_gate`/`policy_rejected` items with a `_policy_detail()` helper that surfaces decision, candidate worker, reasons, and approval authority from `policy_results`. `test_flight_board_maps_policy_queues` and `test_attention_queue_includes_policy_results_with_reasons` cover both. |
| 2 | Source drift and dead-letter queue pressure produce explicit attention items while preserving the read-only/no-write contract | PASS | `get_attention_queue()` takes `drift`/`dead_letter` params and adds `source_drift`/`dead_letter_queue`/`dead_letter_error` items. `get_dead_letter_summary()` reuses `dead_letter_queue.queue_depth()` (read-only) rather than reimplementing queue-scanning logic, and degrades gracefully (`error` field) on an unreadable queue file instead of crashing. Both structural no-write tests (`test_module_never_writes_to_map_state`, `test_rendering_module_never_writes_to_map_state`) still pass unchanged. |
| 3 | Focused mission-control tests and MAP validators pass | PASS | `test_mission_control_tui.py`: 20/20. Full suite: `run_tests.sh` pass=50 fail=0 total=50. `validate_task_mirrors.py`, `validate_events.py --fail-on-new` (errors=0, new_warnings=0) both clean. |

## Files Reviewed

- `MAP_System/scripts/mission_control_tui.py`
- `MAP_System/scripts/_mission_control_app.py`
- `MAP_System/tests/test_mission_control_tui.py`
- `MAP_System/tasks/TASK-164.json`

## Forbidden Changes Check

- PASS: no self-review; reviewer `claude-lab-zera` is not owner `codex-lab-mozu`.
- PASS: changes match the task's declared `output_paths` exactly (all 3 files, same as TASK-160's original set — no scope creep into unrelated files).
- PASS: no new write path introduced — verified independently by re-reading both modules' full source, not just trusting the existing structural tests.

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/scripts/mission_control_tui.py` | YES — declared output path |
| `MAP_System/scripts/_mission_control_app.py` | YES — declared output path |
| `MAP_System/tests/test_mission_control_tui.py` | YES — declared output path |

## Verification

Commands run:

```bash
python3 MAP_System/tests/test_mission_control_tui.py
bash MAP_System/scripts/run_tests.sh
python3 MAP_System/scripts/validate_task_mirrors.py
python3 MAP_System/scripts/validate_events.py --fail-on-new
```

Results:

- Focused tests: 20/20 pass.
- Full suite: pass=50 fail=0 total=50.
- Task mirrors: pass.
- Events: errors=0, new_warnings=0.

## Findings

No BLOCKER or REQUIRED findings.

## Notes

Clean, well-scoped follow-on to TASK-160. `_policy_detail()`'s fallback
string ("pre-dispatch policy result present; inspect runner policy_results")
for a gated/rejected task_id with no matching `policy_results` entry is a
reasonable degrade-gracefully choice rather than a crash — worth keeping in
mind if TASK-163's policy checker output shape ever changes, but not a
blocker here. Good instinct reusing `dead_letter_queue.queue_depth()`
instead of re-parsing the JSONL directly.
