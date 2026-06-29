<!-- hpom: file: templates/review-record.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: validate_review.py field requirements -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: templates/review.md -->
<!-- hpom: superseded_by: NONE -->

# Review Record: [TASK-NNN]

## Header

```
task_id:      TASK-NNN
reviewer:     [reviewer-agent-id]
review_date:  YYYY-MM-DD
task_owner:   [owner-agent-id]
```

Reviewer ([reviewer-agent-id]) ≠ task owner ([owner-agent-id]). Independence check passes.

---

## Verdict

```
[APPROVED | CHANGES_REQUESTED | BLOCKED]
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | [criterion text] | PASS / FAIL / PARTIAL | [how you verified it] |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| [Forbidden change from task definition] | NOT BROKEN / VIOLATED |

---

## Files Reviewed

- `path/to/file.py`

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `path/to/file.py` | YES / NO — reason |

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| [risk description] | HIGH / MEDIUM / LOW | [action] |

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| BLOCKER / REQUIRED / RECOMMENDED / OPTIONAL | `file.py:line` | section | finding | action |

No BLOCKER or REQUIRED findings.

---

## Notes

[Short context, assumptions, or non-blocking observations.]
