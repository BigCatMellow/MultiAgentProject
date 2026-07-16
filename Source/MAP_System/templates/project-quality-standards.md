# Project Quality Standards: [PROJECT_NAME]

Copy this file into `Projects/<PROJECT_NAME>/shared/quality-standards.md`
and fill in the project-specific sections.

---

## Project Type

```
type: software | writing | research | design | operations
```

---

## Positive Standards

What good work looks like for this project. Reviewers check against these.

### Software Projects

- Code changes include tests for new behavior.
- Acceptance criteria are observable and verifiable by command or inspection.
- Output paths match what actually changed.
- No secrets, keys, or credentials in committed files.
- Scripts are runnable standalone without undocumented side effects.

### Writing Projects

- Prose matches the voice baseline established in reference chapters.
- No filter verbs where direct action or sensation can be stated instead.
- No over-explained emotional beats (show consequence, not label).
- Character agency is self-originated, not assigned by plot device.
- No forbidden patterns from `Story_Files/forbidden_patterns.md`.

### Research Projects

- Claims cite a source or are flagged as inferences.
- Scope is explicitly bounded; out-of-scope observations are separated.
- Uncertainty is stated, not hidden.

### Design Projects

- Decisions are documented in `shared/decisions.md`.
- Trade-offs are visible, not buried.
- Open questions are named and owned.

### Operations Projects

- Runbook steps are tested and reproducible.
- Rollback path is defined before execution.
- Health check is defined for each change.

---

## Anti-Patterns

What bad work looks like. Reviewers flag these as REQUIRED or BLOCKER findings.

### All Projects

- Work done outside task `output_paths`.
- Acceptance criteria left unchecked in the review record.
- Self-review (reviewer = task owner).
- Decisions recorded only in chat, not in `shared/decisions.md`.
- Tasks promoted to READY with empty required fields.
- Stale shared files used as authority without verifying freshness.

### Software Anti-Patterns

- Broad changes introduced under a narrow task title.
- Tests that mock the real system in ways that hide real failures.
- Scripts that require undocumented setup.
- Error messages that do not name what failed.

### Writing Anti-Patterns

- Filtering perceptions through a character ("she felt", "he noticed") when the
  sensation can be stated directly.
- Explaining the emotional meaning of an action in the same sentence that shows it.
- Moving a character's agency through plot convenience rather than earned choice.
- Adding clarifying dialogue that reduces ambiguity the story intends.

### Research Anti-Patterns

- Conflating inference with fact.
- Scope expansion without a task update.
- Summarizing source material that contradicts a prior finding without flagging the conflict.

---

## Review Checklist Reference

When reviewing work from this project, use `MAP_System/templates/review-checklist.md`
and add any project-specific checks below.

### Project-Specific Review Checks

- [ ] [Add project-specific check here]
- [ ] [Add project-specific anti-pattern check here]

---

## Quality Owners

| Role | Agent / Person | Scope |
|---|---|---|
| Standards DRI | [command-center or project owner] | Final authority on what quality means |
| Review DRI | [reviewer agent] | Applies standards on each submission |
| Shaping DRI | [architect agent] | Ensures tasks have clear quality targets before execution |
