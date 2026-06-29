# Review Guide

Use this guide when reviewing MAP tasks, artifacts, or code changes.

## Review Goal

Reviews protect project truth and user work. They should find concrete issues,
verify acceptance criteria, and avoid creating vague extra work.

## Verdicts

- `APPROVED` - acceptance criteria are met and no blocker or required findings remain.
- `CHANGES_REQUESTED` - required fixes are needed before approval.
- `BLOCKED` - review cannot complete because required context, files, or verification are missing.

## Severity Levels

- `BLOCKER` - unsafe, data-losing, security-sensitive, or prevents basic function.
- `REQUIRED` - must be fixed to satisfy task intent or acceptance criteria.
- `RECOMMENDED` - useful improvement, but not required for this task.
- `OPTIONAL` - polish or future consideration.

Only `BLOCKER` and `REQUIRED` findings should block approval.

## Review Process

1. Read the task file and acceptance criteria.
2. Read only the listed input and output paths first.
3. Check `shared/current-state.md` for known system issues.
4. Verify the claimed behavior with commands or file inspection when practical.
5. Write findings with file paths and concrete required actions.
6. Record approval or changes requested through the task system and event log.

## Good Findings

Good findings are specific:

- name the affected file;
- describe the observable problem;
- explain the risk;
- state what must change.

Poor findings are vague:

- "This feels wrong."
- "Improve quality."
- "Needs cleanup."
- "Consider refactoring" without a concrete risk.

## Output

Use `templates/review.md` for review artifacts.
