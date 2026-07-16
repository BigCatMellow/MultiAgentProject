# Review: TASK-168 Mission-Control Write-Control Design

```
task_id:      TASK-168
reviewer:     codex-lab-mozu
review_date:  2026-07-14
task_owner:   command-center
builder:      claude-lab-zera
```

Reviewer (`codex-lab-mozu`) is not the builder (`claude-lab-zera`) and is
not listed as task owner. Independence check passes.

## Verdict

```
CHANGES_REQUESTED
```

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Spec covers all 7 disabled keys with the sanctioned command each would call | FAIL | All keys are covered, but `B` names a future/unspecified writer rather than an existing sanctioned command, while the cross-cutting requirement says every sanctioned command already exists. |
| 2 | Every control specifies dry-run/preview text, explicit confirmation, and post-action validators | PARTIAL | The sections contain these fields, but `B` points at a future cost-governance event validator "once built"; that is not an actionable post-action validator for the approved design. |
| 3 | Spec states rollback/non-rollback expectation per control, consistent with change control | PASS | Each control has a rollback/non-rollback bullet and generally follows `CHANGE_CONTROL_SYSTEM.md`'s attribution/reversibility model. |
| 4 | Spec explicitly states design-only; no mission-control code changed by this task | PASS | The artifact states design-only in the purpose section and TASK-168 has only the artifact as an output path. |

## Files Reviewed

- `MAP_System/tasks/TASK-168.json`
- `MAP_System/artifacts/planning/mission-control-write-control-spec.md`
- `MAP_System/artifacts/planning/mission-control-command-center-gap-plan.md`
- `MAP_System/artifacts/planning/mission-control-tui-spec.md`
- `MAP_System/artifacts/planning/map-kill-switch-spec.md`
- `MAP_System/artifacts/planning/map-validator-halt-state-spec.md`
- `MAP_System/CHANGE_CONTROL_SYSTEM.md`
- `MAP_System/scripts/validate_protocol.py`
- `MAP_System/scripts/cost_governance.py`

## Forbidden Changes Check

- PASS: no self-review.
- PASS: TASK-168 declares only a design artifact as output.
- PASS: no TASK-168-scoped implementation in `mission_control_tui.py` or `_mission_control_app.py`.

## Findings

1. REQUIRED: `B` budget bump does not name a currently sanctioned command.

   Evidence: `mission-control-write-control-spec.md` lines 98-105 say the
   override should be written through "whichever script" a future
   implementation exposes, and line 109 says the validator exists "once
   built." Lines 163-166 then state every sanctioned command named above
   already exists in the repo and that missing commands must be designed and
   reviewed before the TUI calls them.

   Required fix: choose an existing bounded behavior for `B` now, such as
   "request-only: emit a command-center approval request and do not mutate
   budget state," or name an actual existing `cost_governance.py` command
   with concrete arguments and validator evidence. If the writer is not
   built, the spec should mark `B` explicitly blocked/deferred rather than
   presenting it as a callable control.

2. REQUIRED: `K` kill/suspend proposes an hcom `!HALT` message that conflicts
   with the currently operative MAP protocol validator.

   Evidence: `mission-control-write-control-spec.md` lines 61-65 specify
   `hcom send ... -- "!HALT ..."`. `validate_protocol.py` recognizes only
   `!ACK`, `!LGTM`, `!ERR`, `!REQ`, `!WARN`, and `!NOTE`; a smoke check of
   `python3 MAP_System/scripts/validate_protocol.py "!UNKNOWN_TOKEN this should fail"`
   confirmed unknown `!` tokens fail. TASK-162's validator comments also state
   the fuller Guidelines token set is aspirational/future, not the operative
   protocol.

   Required fix: replace `!HALT` with an operative shape, likely `--intent
   request` plus a well-formed `!REQ halt ...` or the operator request format
   if a human decision is needed. If `!HALT` is intended to become sanctioned,
   this spec needs to name the prerequisite protocol-extension task before the
   TUI can use it.

## Verification

Commands run:

```bash
python3 MAP_System/scripts/map_task.py show TASK-168
python3 MAP_System/scripts/map_task.py log TASK-168
python3 MAP_System/scripts/validate_protocol.py "!UNKNOWN_TOKEN this should fail"
```

Results:

- Task is `SUBMITTED` with the single declared output path.
- Task log confirms design-only submission.
- Protocol smoke failed unknown `!` token as expected, supporting finding 2.

