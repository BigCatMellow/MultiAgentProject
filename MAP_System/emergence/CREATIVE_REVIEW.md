# Creative Review

## Purpose

Creative review evaluates emergence artifacts — insights, syntheses, ideas, experiments — before they are promoted into HPOM work.

This is not the same as an HPOM task review. HPOM reviews check whether work meets acceptance criteria. Creative review checks whether an idea is worth turning into work at all.

---

## Insight quality criteria

An insight is worth preserving if it is:

- **Relevant** — connected to current or recent work
- **Specific** — describes a concrete pattern, gap, or combination
- **Actionable** — points toward something that could be tested or built
- **Evidence-connected** — grounded in something observed, not speculative
- **Aligned** — consistent with project intent and active priorities
- **Safe to explore** — low enough risk to experiment with, or important enough to escalate

An insight should be parked or dismissed if it is:

- Vague or too broad
- Unrelated to current project direction
- Based on weak or single-point evidence
- A distraction from higher-priority work
- Actually a project-direction decision that needs the Human Owner
- Unsafe to act on without major approval

---

## Do-not-derail rules

Creativity is allowed. It must not become scope creep.

```
1. Do not abandon the assigned task because a better idea appeared.
2. Do not modify out-of-scope files to pursue an insight.
3. Do not treat an insight as a decision.
4. Do not treat a proposal as accepted.
5. Do not rewrite project direction without the Decision Owner.
6. Do not create unlimited insight records from one task unless requested.
7. Do not use creativity to avoid completing review, release, or validation.
8. Do not promote an idea without evidence, review, or approval.
```

The agent's job is:
```
Finish the assigned task.
Capture the emergent idea.
Route the idea safely.
```

---

## What agents should do at a eureka moment

When useful conceptual breakthrough happens mid-task:

1. Continue the assigned task unless the insight reveals a serious risk.
2. Avoid out-of-scope edits.
3. Capture the insight using `templates/INSIGHT_TEMPLATE.md`.
4. Record what triggered the idea.
5. Record what existing pieces combine to create the new possibility.
6. State why it might matter.
7. State the smallest safe experiment.
8. Route the idea — do not silently act on it.

If the insight reveals a conflict, safety issue, or major contradiction with active decisions, follow the conflict protocol (`MAP_System/scripts/flag_conflict.py`).

---

## Review routing by scope

| Scope | Who reviews |
|---|---|
| Inside current task | Task DRI can accept or park |
| Adjacent to current task | Task DRI creates an insight record; routes to operator |
| Project-level idea | Routes to Project DRI or Human Owner |
| MAP system improvement | Routes to core agent review + operator approval before promotion |

---

## When to escalate to the Human Owner

Escalate if the insight:

- Reveals a contradiction in stated project goals
- Suggests changing the direction of active high-priority work
- Requires a decision that modifies shared HPOM gates or approval rules
- Has a risk profile the agent cannot assess without human judgment

Do not escalate for routine synthesis, parked ideas, or low-risk experiments.

---

## Review record

For MAP-level ideas promoted to HPOM tasks, a brief review note is required.

It should state:
- What the idea is
- What evidence supports it
- What experiment was run (if any)
- Who reviewed it
- Decision: promote / park / reject

This does not need to be long. One paragraph is sufficient for routine promotions.
