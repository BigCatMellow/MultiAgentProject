# Review: TASK-170 Propagate Trace IDs Through MAP Lifecycle Events

```
task_id:      TASK-170
reviewer:     claude-lab-zera
review_date:  2026-07-14
task_owner:   codex-lab-mozu
```

Reviewer (claude-lab-zera) != task owner (codex-lab-mozu). Independence
check passes.

## Verdict

```
APPROVED
```

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | New task-scoped event emitters include a stable trace_id convention without rewriting legacy events | PASS | `scripts/event_trace.py`'s `trace_id_for_task()` produces a stable `task:<task_id>` convention; `add_trace_fields()` is called from `map_task.py`, `release_task.py`, `dead_letter_queue.py`, `liveness_reaper.py`, `local_runner.py`, `aider_wrapper.py` at their existing event-emission points — additive only, no historical `events.jsonl` lines touched. |
| 2 | Event validation continues to allow legacy events but rejects malformed trace fields when present | PASS | `scripts/validate_events.py` itself is untouched (correctly not in `output_paths` — it already had this exact behavior from TASK-149's `TRACE_FIELDS` design, which this task reuses rather than reimplementing). New test `test_task_trace_id_convention_causes_no_warning` confirms the specific `task:TASK-N` shape validates cleanly; existing malformed/parent-without-trace-id tests still pass unchanged. |
| 3 | Mission-control event/drilldown rendering shows trace IDs when available and remains compatible with events that lack them | PASS | `render_event_lines()` shows `trace=<id>` when present and `trace=-` for legacy events lacking one (`test_render_event_lines_handles_missing_trace_id`); drilldown rendering covers task/agent/attention/event cases. |
| 4 | Focused tests and full MAP validators pass | PASS | `test_event_trace.py` 5/5, `test_validate_events.py` 7/7, `test_mission_control_tui.py` 27/27. Full suite: `run_tests.sh` pass=52 fail=0 total=52. `validate_task_mirrors.py` and `validate_events.py --fail-on-new` (errors=0, new_warnings=0) both clean. |

## Files Reviewed

All 13 declared output paths, with particular attention to:

- `MAP_System/scripts/event_trace.py` (new, small, single-purpose)
- `MAP_System/scripts/map_task.py`, `release_task.py`, `dead_letter_queue.py`, `liveness_reaper.py` (import wiring)
- `MAP_System/scripts/aider_wrapper.py`, `local_runner.py` (import wiring — see note below)
- `MAP_System/scripts/mission_control_tui.py`, `_mission_control_app.py` (trace rendering)
- `MAP_System/tests/test_event_trace.py`, `test_validate_events.py`, `test_mission_control_tui.py`

## Forbidden Changes Check

- PASS: no self-review; reviewer `claude-lab-zera` is not owner `codex-lab-mozu`.
- PASS: changed files match declared `output_paths`.
- PASS: `validate_events.py`'s core schema/validation logic is unchanged — this task composes TASK-149's existing `TRACE_FIELDS` mechanism rather than duplicating or altering it.

## Scope Check

All 13 output paths are directly relevant to trace-ID propagation and its
rendering/testing — no unrelated files touched.

## Verification

Commands run:

```bash
python3 MAP_System/tests/test_event_trace.py
python3 MAP_System/tests/test_validate_events.py
python3 MAP_System/tests/test_mission_control_tui.py
bash MAP_System/scripts/run_tests.sh
python3 MAP_System/scripts/validate_task_mirrors.py
```

Results: all green, full suite pass=52 fail=0 total=52.

## Findings

No BLOCKER or REQUIRED findings.

One thing I checked and confirmed was NOT a bug: `aider_wrapper.py` and
`local_runner.py` import `event_trace` with a bare
`from MAP_System.scripts.event_trace import ...` (no try/except fallback),
unlike `map_task.py`/`release_task.py`/`dead_letter_queue.py`/
`liveness_reaper.py` which got the try/except fix after the earlier
direct-script-execution break. I verified both files run fine as direct
scripts (`--help` works) because they already had a pre-existing
`sys.path.insert(0, str(REPO))` line before the import, from before this
task. Inconsistent style across the six files, but not a functional gap —
confirmed empirically, not just by inspection.

## Notes

Good instinct not touching `validate_events.py` itself — this task's value
is wiring the existing schema/validator into more emitters, not extending
the schema again. The `task:<task_id>` trace-ID convention is simple and
sufficient for this phase (groups by task, which is the causal-chain unit
that matters most right now); a future task can extend to
sub-task/attempt-scoped trace IDs if needed without breaking this
convention.
