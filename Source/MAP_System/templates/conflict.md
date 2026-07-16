# Conflict Record: [CONFLICT-NNN]

## Header

```
conflict_id:    CONFLICT-NNN
raised_by:      [agent-id]
raised_at:      YYYY-MM-DD
affected_task:  TASK-NNN
status:         OPEN | RESOLVED
decision_owner: [human or agent with authority to resolve]
```

When this record is created, the affected task must move to CONFLICT status.
The task cannot resume until `status: RESOLVED` and `resolution` is populated.

---

## Conflict Type

```
AUTHORITY_CONFLICT        — two source documents say contradictory things
SCOPE_CONFLICT            — two active tasks claim the same output path
STATE_CONFLICT            — SQLite and task JSON disagree on task state
DECISION_CONFLICT         — a new decision contradicts an existing decision
FACTUAL_CONFLICT          — a review finding contradicts the task submission
```

---

## Conflicting Sources

| Source A | Source B |
|---|---|
| `[file path or document]` | `[file path or document]` |
| "[exact quote or claim]" | "[exact quote or claim]" |

---

## Affected Files

- `[path to file affected by or containing the conflict]`

---

## Impact

[What breaks or stays blocked until this is resolved. Who is waiting.]

---

## Resolution

```
status:       RESOLVED
resolved_by:  [agent-id or "command-center"]
resolved_at:  YYYY-MM-DD
decision_ref: DEC-NNN (if a new decision was recorded)
```

Resolution statement:

[What was decided. Which source is authoritative. What changes as a result.]

---

## Follow-up Tasks

- [ ] [Any tasks created to implement the resolution]
