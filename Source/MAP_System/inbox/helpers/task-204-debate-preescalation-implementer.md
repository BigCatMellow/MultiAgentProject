# Work Packet: TASK-204 — Optional debate pre-escalation step

- Task: TASK-204 (READY). Owner of record: gune. You are the delegated
  implementer (scoped doc edit). A different core agent reviews.
- Source: IDEA-0019 / PROMO-0009. This is DOC + CONVENTION ONLY. Additive,
  opt-in, non-breaking.

## Do exactly this

Edit ONLY these two files (they are the task's files_in_scope):
1. `MAP_System/DECISION_AUTHORITY_SYSTEM.md`
2. `MAP_System/notes/review-guide.md`

### Edit 1 — DECISION_AUTHORITY_SYSTEM.md

Insert a new subsection immediately BEFORE the `## Related files` heading
(i.e., after the `## Relationship to other systems` section). Use this text
verbatim (adjust surrounding blank lines to match the file's style):

```
## Optional: debate pre-escalation (IDEA-0019 / TASK-204)

Before escalating a contested decision to the operator, an agent MAY run a
structured multi-perspective critique using the existing `hcom run debate`
workflow. This is **opt-in and additive**: it does not replace, gate, or
change any existing escalation or conflict-resolution path. If debate is not
used, every current path behaves exactly as before.

Use it to pressure-test a decision when reviewers genuinely disagree, not as a
routine step. When a debate informs a decision, cite it in the decision or
conflict-resolution record (e.g. "debate: <thread/summary>") so the reasoning
is durable.

See `notes/review-guide.md` ("When to invoke debate") for when this is worth
the cost.
```

### Edit 2 — notes/review-guide.md

Add a new section at the END of the file (after the `## Output` section) using
this text verbatim:

```
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
```

## Must-not
- Do not touch `scripts/flag_conflict.py` or any escalation/gate behavior.
- Do not add a new script or command; reference `hcom run debate` directly.
- Do not make debate mandatory or a gate anywhere.
- Do not edit any file outside the two named above.
- Do not commit, push, approve, or release. Do not run `map_task.py approve`.

## Verify, then report
- Confirm both edits are in place and no other file changed
  (`git -C /home/home/Projects/MultiAgentProject status --short`).
- Run `python3 MAP_System/scripts/validate_task_mirrors.py` and report the
  result line.
- Reply in hcom to @gune: "TASK-204 draft done" + the two files + the validate
  line. Then STOP — do not submit the task; gune assigns the reviewer.
