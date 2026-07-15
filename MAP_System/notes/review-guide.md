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

## Claim Before Reviewing (TASK-199 / IDEA-0017)

Multiple agents can see the same SUBMITTED task and start a full independent
review before either one finalizes — an hcom "I'm taking this review"
message can lose the race against a broadcast, and duplicate review work
gets thrown away. Before starting substantive review work on a task, claim
it atomically:

```python
from MAP_System.db.claims import claim_review
claim_review("TASK-NNN", "your-agent-id")  # True = claimed, False = already claimed / self-review / not SUBMITTED
```

`claim_review` returns `False` without raising when the task isn't
`SUBMITTED`, the reviewer is the task owner (self-review), or another
reviewer already holds an open claim — check the return value and stand
down if `False`. `map_task.py approve`/`reject` best-effort releases any
open claim the acting reviewer holds, so no separate release call is
required in the normal flow. This is optional, not gated: a reviewer who
skips claiming can still approve/reject normally, and a second independent
review that reaches the terminal action first will still win cleanly (the
task's status transition itself was already atomic) — claiming just avoids
wasting the work of the reviewer who would otherwise lose that race.

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

## When to Invoke Debate (IDEA-0019 / TASK-204)

`hcom run debate` runs a structured multi-perspective critique. It is an
OPTIONAL pre-escalation tool, not a required review step.

Invoke it when:

- A task is CONFLICT-frozen (`scripts/flag_conflict.py`) and the resolution is
  genuinely contested — two defensible readings, no clear winner.
- A high-authority `DECISION_CLASSES` call is close and a single reviewer's
  verdict would feel under-tested.
- Two reviewers reach opposite verdicts and you would otherwise escalate
  straight to the operator.

Do NOT invoke it for routine reviews, clear-cut findings, or to avoid making a
call you can already make. Debate costs tokens and time; use it where
multi-perspective critique actually changes the outcome. If a debate informs
the result, cite it in the review/decision/conflict record.
