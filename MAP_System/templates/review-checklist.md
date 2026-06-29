# Review Checklist

Use this alongside `MAP_System/templates/review-record.md`.
This checklist is the mechanical pass; the review record captures findings.

---

## 1. Scope Check

- [ ] Changed files match the task's `output_paths`
- [ ] No files changed outside scope (check git diff or submission notes)
- [ ] Forbidden changes were not made

If any scope violation: mark BLOCKER in review record.

---

## 2. Acceptance Criteria Check

For each criterion in the task file:

- [ ] Criterion 1: [paste text] — tested how?
- [ ] Criterion 2: ...
- [ ] All criteria are testable by command, inspection, or direct observation
- [ ] No criteria are assumed satisfied without evidence

If any criterion fails: mark REQUIRED in review record.

---

## 3. Forbidden Changes Check

- [ ] `Pathwell.txt` not edited (writing projects)
- [ ] No secrets or credentials added
- [ ] No task dependencies bypassed
- [ ] [Project-specific forbidden changes from task file]

---

## 4. No-Self-Review Check

- [ ] Reviewer agent ID ≠ task owner agent ID
- [ ] For high-risk tasks: reviewer is from a different model family or is human

If self-review: this review is invalid. A different reviewer must be assigned.

---

## 5. Quality Standards Check

Reference: `Projects/<PROJECT_NAME>/shared/quality-standards.md`

- [ ] Output matches project positive standards
- [ ] No anti-patterns present

Flag each anti-pattern found as RECOMMENDED or REQUIRED depending on severity.

---

## 6. Risk Identification

- [ ] New risks introduced by this task are named
- [ ] Risks from review findings are captured in the review record
- [ ] Follow-up tasks are created or recommended for unresolved risks

---

## 7. Evidence Completeness

- [ ] Files reviewed are listed in the review record
- [ ] Verification commands run and results recorded
- [ ] Findings table complete (even if empty)

---

## Verdict Decision

| Condition | Verdict |
|---|---|
| All criteria pass, no BLOCKER or REQUIRED findings | APPROVED |
| Any criterion fails OR any REQUIRED finding | CHANGES_REQUESTED |
| Any BLOCKER finding OR scope violation | BLOCKED |
| Self-review detected | INVALID — reassign reviewer |
