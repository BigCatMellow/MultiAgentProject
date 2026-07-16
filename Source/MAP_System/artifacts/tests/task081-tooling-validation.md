# TASK-081 Tooling Validation

Owner: codex-lab-limo
Date: 2026-07-02

## Implemented

- `map_task.py rework` returns a `CHANGES_REQUESTED` task to `READY` through
  a first-class CLI transition.
- `validate_task_graph.py` ignores known shared/generated outputs for active
  output-collision checks:
  - `MAP_System/events/events.jsonl`
  - `MAP_System/emergence/INDEX.md`
  - `MAP_System/workflow/task_graph.json`
- `map_metrics.py` groups legacy event aliases into canonical metric counts:
  - `REVIEW_APPROVED` -> `APPROVED`
  - `REVIEW_CHANGES_REQUESTED` -> `CHANGES_REQUESTED`
  - `task_progress` -> `PROGRESS`
- `map_task.py` already had the F9 create-time warning for self-owned
  review-shaped tasks; TASK-081 adds regression coverage for that behavior.

## Focused Tests

Passed:

- `python3 MAP_System/tests/test_map_task_rework.py`
- `python3 MAP_System/tests/test_validate_task_graph_shared_outputs.py`
- `python3 MAP_System/tests/test_map_metrics_aliases.py`

## Full Suite Status

`MAP_System/scripts/run_tests.sh` reports:

- `pass=22 fail=0 total=22`

The earlier ownership-state blocker was resolved when claude-lab-rose reviewed
and approved TASK-065. Final task graph validation is clean.

## Other Validators

Passed:

- `python3 MAP_System/scripts/validate_events.py`: 0 errors, 33 historical warnings.
- `python3 MAP_System/scripts/map_emergence.py validate`: 19 artifacts checked.
- `python3 MAP_System/scripts/map_emergence.py stale`: no findings.
- `python3 MAP_System/scripts/map_metrics.py --json`: event aliases grouped in
  the metrics output.

## Emergence Closeout

INS-0007 is now `PROMOTED` with a lifecycle close-out note. The insight's
recommended stale-record report and lifecycle habit were implemented through
TASK-065, TASK-075, TASK-078, and TASK-081.
