# Review Record: TASK-040

## Header

```
task_id:      TASK-040
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
| 1 | CONFLICT is a valid task status in SQLite | PASS | SQLite stores task status as text; `flag_conflict.py` updates tasks to `CONFLICT`; `flag_conflict.py` terminal statuses include `RELEASED` |
| 2 | `flag_conflict.py` creates a conflict record and moves task to CONFLICT | PASS | Code path creates a conflict Markdown record and updates the task status |
| 3 | Conflict template includes type, affected_files, conflicting_sources, decision_owner, resolution | PASS | `templates/conflict.md` includes those fields/sections |
| 4 | Tasks in CONFLICT cannot be claimed or promoted without resolution record | FAIL | A temp DB with HPOM-complete `TASK-038` set to `CONFLICT` was promoted to `READY` by `promote_task.py` without any resolution record |

## Files Reviewed

- `MAP_System/scripts/flag_conflict.py`
- `MAP_System/templates/conflict.md`
- `MAP_System/scripts/promote_task.py` behavior against CONFLICT
- `MAP_System/tasks/TASK-040.json`

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| REQUIRED | `MAP_System/scripts/promote_task.py` or conflict gate layer | promotion from `CONFLICT` | `promote_task.py` can move a HPOM-complete task from `CONFLICT` to `READY` with no resolution record, violating the freeze criterion. | Add a promotion guard for `CONFLICT` tasks unless a resolution record exists, and add a regression test. |

## Verification

```bash
python3 MAP_System/scripts/promote_task.py --db "$tmp/map.db" --root "$tmp" --task-id TASK-038 --no-sync
# {"task_id":"TASK-038","status":"READY"}
```
