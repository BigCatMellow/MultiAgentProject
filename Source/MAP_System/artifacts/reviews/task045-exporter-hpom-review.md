# Review Record: TASK-045

## Header

```
task_id:      TASK-045
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
| 1 | HPOM fields in a task JSON survive a sync round-trip | PASS | `objective`, `reviewer_role`, `risk` all present after export; test asserts each |
| 2 | Existing task JSON fields not in SQLite schema are preserved | PASS | `input_paths` (not in SQLite) preserved from existing JSON; test asserts `["MAP_System/shared/hpom.md"]` |
| 3 | Tests verify round-trip preservation of objective, reviewer_role, risk | PASS | `test_hpom_fields_survive_export` asserts all three explicitly |
| 4 | run_tests.sh still passes | PASS | SUMMARY pass=7 fail=0 total=7 |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Do not break existing tests | NOT BROKEN — 7/7 pass |

---

## Files Reviewed

- `MAP_System/migration/export_to_files.py`
- `MAP_System/tests/test_exporter_hpom_fields.py`
- `MAP_System/artifacts/tests/exporter-hpom-fields-test.md`
- `MAP_System/tasks/TASK-045.json`

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/migration/export_to_files.py` | YES |
| `MAP_System/tests/test_exporter_hpom_fields.py` | YES |
| `MAP_System/artifacts/tests/exporter-hpom-fields-test.md` | YES |
| `MAP_System/tasks/TASK-045.json` | YES |

All changes inside scope.

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| If an existing task JSON contains a stale HPOM field value that contradicts the promoted version, export now preserves the stale value (no conflict detection) | LOW | Acceptable: `promote_task.py` is the write gate for HPOM fields; the exporter is read-only relative to them |
| First sync for a brand-new task that has no JSON file yet: `read_json` returns `{}`, HPOM fields are empty in output | LOW | Correct behavior — HPOM fields are added by `promote_task.py` before any sync; no gap in practice |

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| OPTIONAL | export_to_files.py:104 | `task_file_payload` | `description` has special fallback logic (`task.get("description") or existing.get(...)`) but other canonical fields like `title` don't — if SQLite had an empty title, it would overwrite a non-empty existing title | Not a real scenario now; note the asymmetry if the schema ever allows empty titles |

No BLOCKER or REQUIRED findings.

---

## Notes

The merge strategy is correct and minimal: read existing JSON → overlay canonical SQLite fields → write. HPOM fields survive because they are in `existing` and never referenced by name in `payload.update(...)`. This removes the `--no-sync` workaround requirement going forward.

The `promote_task.py --no-sync` path used by Codex for TASK-036 is now unnecessary for normal operation. Existing task JSONs that already have HPOM fields (TASK-036.json, etc.) will continue to round-trip correctly through future syncs.
