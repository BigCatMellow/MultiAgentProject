<!-- hpom: file: artifacts/releases/task-201-release-checklist.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: HPOM-006 release gate -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Release Checklist: TASK-201

## Header

```
task_id:      TASK-201
released_by:  codex-lab-nivo
release_date: 2026-07-15
reviewed_by:  claude-lab-toku
```

## Checklist

- [x] Shared-file updates complete
- [x] Decisions recorded
- [x] Follow-up tasks created
- [x] Event log entry prepared
- [x] Emergence capture considered

## Summary

TASK-201 ships the bounded halt-authority window mechanism disabled by
default. `runtime_policy.yaml` now has a `halt_authority_window` block with
`enabled_until: null`, and the Layer 1 and protocol validators preserve
telemetry-only behavior unless an operator enables a future-dated scoped
window.

- Shared files: `MAP_System/workflow/runtime_policy.yaml`,
  `MAP_System/scripts/halt_state.py`,
  `MAP_System/scripts/validate_layer1.py`,
  `MAP_System/scripts/validate_protocol.py`,
  `MAP_System/tests/test_halt_authority_window.py`,
  `MAP_System/notes/halt-authority-window-runbook.md`, and
  `MAP_System/scripts/run_tests.sh`.
- Decisions: no policy decision changed. Enabling the window remains an
  operator action documented in the runbook.
- Follow-ups: no new task required. The mechanism unlocks a later C1/V
  measurement window once the operator chooses to enable it.
- Events: submission, approval, and release are recorded in
  `events/events.jsonl`.
- Emergence: considered. This implements the promoted measurement gap from
  the robustness grading work; no separate emergence artifact is needed.

## Verification

- `MAP_System/scripts/run_tests.sh`: 67/67 pass.
- `MAP_System/tests/test_halt_authority_window.py`: 5/5 pass.
- `MAP_System/tests/test_validate_layer1.py`: pass.
- `MAP_System/tests/test_validate_protocol.py`: pass.
- `MAP_System/scripts/validate_task_mirrors.py`: pass.
- `MAP_System/scripts/validate_task_graph.py`: pass.
- `MAP_System/scripts/validate_events.py --fail-on-new`: pass.
- Independent review: `artifacts/reviews/task201-review-toku.md`.
