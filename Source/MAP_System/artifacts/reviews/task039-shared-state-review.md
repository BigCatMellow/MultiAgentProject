# Review Record: TASK-039

## Header

```
task_id:      TASK-039
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
| 1 | `validate_shared_state.py` finds and reports shared/ files missing required metadata | FAIL | A temp file missing `project`, `verified_against`, `supersedes`, and `superseded_by` returned OK because the script treats those fields as optional |
| 2 | STALE or SUPERSEDED status is flagged with file path and reason | PASS | Existing shared run reports `NEEDS_REVIEW` warnings with paths; strict mode exits 1 when warnings exist |
| 3 | Template includes all required metadata fields | PASS | `templates/shared-state.md` includes all HPOM metadata fields |
| 4 | Script can be run standalone | PASS | `python3 MAP_System/scripts/validate_shared_state.py` exits 0 on current shared files |

## Files Reviewed

- `MAP_System/scripts/validate_shared_state.py`
- `MAP_System/templates/shared-state.md`
- `MAP_System/tasks/TASK-039.json`

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| REQUIRED | `MAP_System/scripts/validate_shared_state.py` | `REQUIRED_FIELDS` / `OPTIONAL_FIELDS` | The task description defines the full metadata header as required, but the validator treats `project`, `verified_against`, `supersedes`, and `superseded_by` as optional. | Treat all required HPOM header fields from the template/task contract as required, or update the task contract and acceptance criteria to explicitly narrow the required set. |

## Verification

```bash
python3 MAP_System/scripts/validate_shared_state.py
# 16 file(s) checked. 0 failure(s). 3 warning(s).

python3 MAP_System/scripts/validate_shared_state.py --shared-dir "$tmp"
# OK for a file missing several declared metadata fields
```
