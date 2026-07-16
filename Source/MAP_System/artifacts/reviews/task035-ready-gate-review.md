# Review Record: TASK-035

## Header

```
task_id:      TASK-035
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
| 1 | promote_task.py rejects READY transition when any required HPOM field is missing | PASS | test_invalid_task_blocked passes; audit flags TASK-036 for missing 7 HPOM fields |
| 2 | Error message names the missing field | PASS | CLI stderr output: `missing=json.objective,json.required_context,...`; test_cli_error_names_missing_field passes |
| 3 | claim_task in db/claims.py fails on READY tasks missing required fields | PASS | Soft gate added at lines 39–50: checks task_acceptance_criteria before allowing claim |
| 4 | pytest tests pass for valid and invalid promotion cases | PASS | 3 deterministic tests pass directly with `python3`; wired into run_tests.sh |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Do not break existing tests | NOT BROKEN — run_tests.sh: pass=5 fail=0 total=5 |

---

## Files Reviewed

- `MAP_System/scripts/promote_task.py`
- `MAP_System/db/claims.py`
- `MAP_System/scripts/map_task.py`
- `MAP_System/tests/test_promote_task.py`
- `MAP_System/scripts/run_tests.sh`
- `MAP_System/artifacts/tests/promote-task-test.md`

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/scripts/promote_task.py` | YES — output_path |
| `MAP_System/db/claims.py` | YES — output_path |
| `MAP_System/scripts/map_task.py` | YES — output_path |
| `MAP_System/tests/test_promote_task.py` | YES — output_path |
| `MAP_System/scripts/run_tests.sh` | YES — wiring tests in, no architectural change |
| `MAP_System/artifacts/tests/promote-task-test.md` | YES — verification artifact |

All changes inside scope.

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| Existing tasks (035-043) fail audit since they predate HPOM JSON fields | LOW | Backfill task JSONs with HPOM fields before promoting; this is expected behavior, not a bug |
| CONFLICT/RELEASED statuses not yet valid task JSON field values in schema | LOW | No action needed now — schema uses unconstrained TEXT; future task validates these transitions |

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| RECOMMENDED | promote_task.py:114–116 | `validate_hpom_contract` | `SQLITE_FIELD_MAP` validates acceptance_criteria in SQLite AND the same field appears in `HPOM_JSON_FIELDS` check — agents will see both `json.acceptance_criteria` and `sqlite.acceptance_criteria` in error output for the same logical gap | Consider deduplicating: remove acceptance_criteria from `HPOM_JSON_FIELDS` since the SQLite check already covers it, or add a comment explaining the intentional double-check |
| RECOMMENDED | promote_task.py | overall | `required_context`, `forbidden_changes`, `expected_artifacts`, `reviewer_role`, `risk` are only validated from JSON, not SQLite. This is correctly noted in the artifact. | Document in promote_task.py docstring that JSON is the HPOM contract source until SQLite schema grows HPOM columns |

No BLOCKER or REQUIRED findings.

---

## Notes

- The `--no-sync` flag is a good addition for tests and dry runs.
- The `--audit` mode correctly flags TASK-036 (expected). This mode will be useful as a routine health check.
- Changing `map_task.py create` default from READY to NEEDS_SHAPING is correct governance behavior and benefits all downstream agents immediately.
- pytest is not installed; the direct-module test pattern is clean and sufficient for this environment.
