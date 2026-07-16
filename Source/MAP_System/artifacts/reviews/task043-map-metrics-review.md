# Review Record: TASK-043

## Header

```
task_id:      TASK-043
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
| 1 | reports task count by status | PASS | `task_counts()` groups by status; text output shows `| APPROVED | 23 |`, `| SUBMITTED | 4 |`, etc.; JSON output includes `task_counts` dict |
| 2 | reports review queue size (SUBMITTED tasks awaiting review) | PASS | `review_queue_size` = `counts.get("SUBMITTED", 0)`; test asserts value=2; live run shows 4 |
| 3 | reports conflict count (tasks in CONFLICT status) | PASS | `conflict_count` = `counts.get("CONFLICT", 0)`; test asserts value=1; live run shows 0 |
| 4 | reports stale shared file count (if validate_shared_state.py exists) | PASS | `stale_shared_count()` calls `validate_shared_state.py --strict` and parses STATUS_STALE/SUPERSEDED/NEEDS_REVIEW lines; test asserts value=1 for a NEEDS_REVIEW file; live run shows 3 |
| 5 | script runs standalone: python3 MAP_System/scripts/map_metrics.py | PASS | Runs cleanly; text and `--json` modes both verified |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Script must be read-only — must not modify project state | NOT VIOLATED — no writes to DB, files, or events; all operations are SELECT or subprocess reads |

---

## Files Reviewed

- `MAP_System/scripts/map_metrics.py`
- `MAP_System/tests/test_map_metrics.py`
- `MAP_System/artifacts/tests/map-metrics-test.md`
- `MAP_System/tasks/TASK-043.json`
- `MAP_System/scripts/run_tests.sh` (confirmed map_metrics_test wired at line 35)

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/scripts/map_metrics.py` | YES |
| `MAP_System/tests/test_map_metrics.py` | YES |
| `MAP_System/scripts/run_tests.sh` | YES — test wiring |
| `MAP_System/artifacts/tests/map-metrics-test.md` | YES |

All changes inside scope.

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| `stale_shared_count` uses `--strict` flag, which counts NEEDS_REVIEW as stale — this inflates the count relative to "truly stale" (STALE/SUPERSEDED only) | LOW | Acceptable: conservative count is safe for a health dashboard; document that NEEDS_REVIEW files appear in count |
| `change_request_rate` is computed from all-time event totals, not per-sprint — a project with many early rejections will always show a high rate even after stabilizing | LOW | Accepted for v1; add a `--since DATE` filter if needed later |
| `stale_shared_count` runs a subprocess each call — if `validate_shared_state.py` is missing, silently returns 0 | LOW | Acceptable: guard `if not VALIDATE_SHARED.exists()` is explicit |

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| OPTIONAL | `map_metrics.py:62` | `event_counts` | `event_counts` dict is computed and included in JSON output but not surfaced in the text table | Add an event counts row or drop from JSON output for consistency — non-blocking |
| OPTIONAL | `map_metrics.py:94` | `print_table` | Table header uses `---:` (right-align) for count column — correct for numbers; verify markdown renderer handles it | Cosmetic; non-blocking |

No BLOCKER or REQUIRED findings.

---

## Notes

Clean, minimal read-only reporting script. The `collect_metrics` / `print_table` / `--json` split is correct. `stale_shared_count` correctly delegates to `validate_shared_state.py` rather than reimplementing metadata parsing. `change_request_rate` is a useful HPOM health signal. Suite 10/10.
