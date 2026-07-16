# Review Record: TASK-041

## Header

```
task_id:      TASK-041
reviewer:     codex-live
review_date:  2026-06-29
task_owner:   claude-mako
```

Reviewer (codex-live) != task owner (claude-mako). Independence check passes.

## Verdict

```
CHANGES_REQUESTED
```

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `validate_decisions.py` parses `shared/decisions.md` and flags entries missing required fields | PASS | Current decisions validate with 0 failures |
| 2 | Decision template includes id, owner, reason, applies_to, date, supersedes, superseded_by | FAIL | `templates/decision.md` lacks these required fields |
| 3 | `DECISIONS.md` is a machine-readable index of active decisions | PASS | `shared/DECISIONS.md` contains a table of active decisions |

## Files Reviewed

- `MAP_System/scripts/validate_decisions.py`
- `MAP_System/shared/DECISIONS.md`
- `MAP_System/templates/decision.md`
- `MAP_System/tasks/TASK-041.json`

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| REQUIRED | `MAP_System/templates/decision.md` | template body | The template does not include the required schema fields `id`, `owner`, `reason`, `applies_to`, `date`, `supersedes`, and `superseded_by`. | Update the template so new decision entries satisfy the validator and the task contract. |

## Verification

```bash
python3 MAP_System/scripts/validate_decisions.py
# 11 decision(s) checked. 11 active. 0 failure(s).
```
