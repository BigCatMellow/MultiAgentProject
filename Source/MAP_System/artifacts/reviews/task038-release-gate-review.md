# Review Record: TASK-038

## Header

```
task_id:      TASK-038
reviewer:     claude-mako
review_date:  2026-06-29
task_owner:   codex-live
```

Reviewer (claude-mako) ≠ task owner (codex-live). Independence check passes.

---

## Verdict

```
APPROVED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | RELEASED status exists in SQLite schema | PASS | `task_release_records` table in `schema.sql` and `db/migration/001_release_gate.sql`; `ensure_schema()` in `release_task.py` creates it idempotently at runtime; status is set via `UPDATE tasks SET status='RELEASED'` |
| 2 | release_task.py enforces checklist before marking RELEASED | PASS | `validate_checklist()` runs before any DB write; checks task_id match and 4 required `[x]` items; `test_incomplete_checklist_blocks_release` confirms incomplete checklist exits 1 and leaves task APPROVED with 0 release records |
| 3 | map_task.py release subcommand works | PASS | `release_task_state()` delegates to `release_task.py` subprocess; `test_map_task_release_subcommand` confirms end-to-end path sets status RELEASED with 1 release record |
| 4 | tasks cannot go APPROVED → RELEASED without a checklist completion record | PASS | `INSERT INTO task_release_records` and `UPDATE tasks SET status='RELEASED'` are in the same `with connect(db_path) as conn:` block (single transaction); no path sets RELEASED without the record |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Do not modify task claiming logic in db/claims.py | NOT CHANGED — claims.py untouched |
| Do not change APPROVED or SUBMITTED status semantics | NOT CHANGED — existing approve/reject/submit paths are unchanged |
| Do not remove existing map_task.py subcommands | NOT CHANGED — create/approve/reject/show all present |

---

## Files Reviewed

- `MAP_System/scripts/release_task.py`
- `MAP_System/scripts/map_task.py` (release_task_state + release subparser)
- `MAP_System/db/migration/001_release_gate.sql`
- `MAP_System/migration/schema.sql` (task_release_records table)
- `MAP_System/templates/release-checklist.md`
- `MAP_System/tests/test_release_gate.py`
- `MAP_System/artifacts/tests/release-gate-test.md`
- `MAP_System/tasks/TASK-038.json`

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/scripts/release_task.py` | YES |
| `MAP_System/scripts/map_task.py` | YES |
| `MAP_System/db/migration/001_release_gate.sql` | YES |
| `MAP_System/migration/schema.sql` | YES |
| `MAP_System/templates/release-checklist.md` | YES |
| `MAP_System/tests/test_release_gate.py` | YES |
| `MAP_System/scripts/run_tests.sh` | YES — test wiring |
| `MAP_System/scripts/validate_task_graph.py` | IN SCOPE — TASK-038 output_paths includes it |
| `MAP_System/artifacts/tests/release-gate-test.md` | YES |

All changes inside scope.

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| `task_release_records` is only created by `ensure_schema()` at runtime — agents running old sessions may not have the table until they call `release_task.py` or `ensure_schema()` explicitly | LOW | The `001_release_gate.sql` migration file and `schema.sql` update mean any fresh DB gets it; existing DBs get it on first `release_task.py` call |
| Checklist regex matches exact strings (e.g., "Shared-file updates complete") — a minor template wording change would silently break validation | LOW | Template and regex strings are in sync in this PR; document that they must move together |
| `release_task_state` in `map_task.py` calls `release_task.py` as subprocess and propagates exit code via `check=True`, but errors from `release_task.py` print to its stderr and the CalledProcessError re-raises without the original message | LOW | Acceptable; the inner error is visible at the terminal even if the outer exception message is generic |

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| RECOMMENDED | `test_release_gate.py` | coverage | No test for "task not APPROVED" path — if a SUBMITTED or READY task is passed to `release_task.py`, `release_task()` raises `ReleaseError`. This path is guarded in code but not exercised by the test suite | Add `test_release_non_approved_blocked` in a follow-up; non-blocking here |
| OPTIONAL | `release_task.py:82` | `append_event` | `append_event` calls `ensure_schema` and `ensure_agent` again inside its own `connect` context — creates a second implicit transaction after the main one. Both are `CREATE TABLE IF NOT EXISTS` / `INSERT OR IGNORE` so idempotent, but could be one transaction | Combine into one `release_task()` transaction in a future cleanup pass |

No BLOCKER or REQUIRED findings.

---

## Notes

The implementation is minimal and correct. The checklist gate (validate → insert record → update status, all in one transaction) is the right pattern. `ensure_schema()` using `CREATE TABLE IF NOT EXISTS` means no migration runner is needed for existing DBs. The four required check strings match exactly between `release_task.py` and `templates/release-checklist.md`, and the test suite verifies both the happy path and the incomplete-checklist block. Suite is now 9/9.
