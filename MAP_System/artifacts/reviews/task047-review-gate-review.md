# Review Record: TASK-047

## Header

```
task_id:      TASK-047
reviewer:     codex-live
review_date:  2026-06-29
task_owner:   claude-mako
```

Reviewer (codex-live) != task owner (claude-mako). Independence check passes.

---

## Verdict

```
CHANGES_REQUESTED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `validate_review.py` exits 0 for well-formed review, 1 for self-review or missing fields | PASS | Temp well-formed review exited 0; temp self-review exited 1 with `SELF_REVIEW` |
| 2 | `map_task.py approve --review-record` blocks APPROVED on `validate_review.py` exit 1 | PARTIAL | Validation is wired only when `--review-record` is supplied; approval without any review record succeeds |
| 3 | `review-record.md` template includes all required HPOM header fields | FAIL | `MAP_System/templates/review-record.md` does not exist; existing `MAP_System/templates/review.md` lacks `task_id`, `reviewer`, `review_date`, and `task_owner` header fields |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Do not allow a task to become APPROVED without a review record | BROKEN — `map_task.py approve TASK-047 --reviewer codex-live` succeeds on a temp DB without `--review-record` |

---

## Files Reviewed

- `MAP_System/scripts/validate_review.py`
- `MAP_System/scripts/map_task.py`
- `MAP_System/templates/review.md`
- `MAP_System/tasks/TASK-047.json`

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| REQUIRED | `MAP_System/scripts/map_task.py` | `set_review_state` / CLI parser | `approve` still permits APPROVED with no review record because `--review-record` defaults to `None` and validation is skipped. Direct temp-DB command returned status 0 and set `TASK-047` to `APPROVED`. | Require `--review-record` for all approvals, or fail in `set_review_state` when `approved` is true and no review record is supplied. |
| REQUIRED | `MAP_System/templates/review-record.md` | Task output path | The required template file is absent. The existing `MAP_System/templates/review.md` is not the declared output and lacks the HPOM header fields needed by `validate_review.py`. | Add `MAP_System/templates/review-record.md` or update the task output path and template so it includes `task_id`, `reviewer`, `review_date`, and `task_owner`. |
| RECOMMENDED | `MAP_System/tests/` | coverage | No regression test covers approval without `--review-record`, so the main HPOM-004 enforcement requirement can silently regress. | Add a focused test proving approval without a review record fails and invalid records block approval. |

---

## Verification

```bash
MAP_System/scripts/run_tests.sh
# SUMMARY pass=7 fail=0 total=7

python3 MAP_System/scripts/validate_review.py --review-record "$tmp/good.md" --task-id TASK-X
# OK review record valid

python3 MAP_System/scripts/validate_review.py --review-record "$tmp/self.md" --task-id TASK-X
# exit 1, SELF_REVIEW

python3 MAP_System/scripts/map_task.py --db "$tmp/map.db" --output-dir "$tmp/out" approve TASK-047 --reviewer codex-live
# exit 0, {"task_id":"TASK-047","status":"APPROVED"} despite no review record
```
