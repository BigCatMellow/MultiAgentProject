# Idea Promotion Rules

## What promotion is

Promotion moves an idea from the Emergence System into the HPOM execution system.

Before promotion: an idea is a candidate. It may not change the project.
After promotion: the idea becomes a task, decision record, or artifact with an owner, review path, and acceptance criteria.

Promotion is a gate, not a default. Most ideas should be tested or parked before promotion.

---

## Promotion path

```
Insight
→ Synthesis (optional but recommended for complex ideas)
→ Idea card
→ Experiment (required if the idea changes existing behavior)
→ Promotion record
→ HPOM task / decision record / shared-state update
```

Short path for simple, low-risk ideas:
```
Insight → Idea card → Promotion record → HPOM task
```

---

## Conditions for promotion

An idea may be promoted only if it has all of the following:

| Field | Required content |
|---|---|
| Clear problem or opportunity | What gap, tension, or capability is this addressing? |
| Connection to existing work | Which tasks, artifacts, or decisions does this connect to? |
| Expected benefit | What specifically improves if this works? |
| Known risk | What could go wrong? |
| Smallest safe experiment | What is the least-destructive test? |
| Owner | Who is accountable for the promoted task? |
| Review path | Who reviews the result? |
| Decision owner (if applicable) | Who has authority to approve project-direction changes? |

An idea is missing any of these → do not promote. Park it or return to experimentation.

---

## What an idea promotes into

Choose the appropriate HPOM artifact:

| What the idea becomes | When to use |
|---|---|
| HPOM task | The idea requires implementation work |
| Decision record | The idea resolves a design question or architecture choice |
| Shared-state update | The idea corrects or extends a current-state or requirements file |
| Project artifact | The idea produces a document, template, or reference material |
| MAP system improvement | The idea improves MAP's own process or tooling |
| Parked reference | The idea is valid but not the right time — record it and stop |

---

## Conditions that block promotion

Do not promote if:

- The idea is only interesting but has no clear benefit.
- The idea lacks evidence from an experiment or real observation.
- The idea duplicates an existing task or decision.
- Promoting it would derail higher-priority work.
- It requires a major project-direction decision that has not been approved.
- The idea cannot be tested safely.
- The experiment result was negative or inconclusive and has not been revised.

---

## Promotion record

Every promotion requires a promotion record using `templates/PROMOTION_RECORD_TEMPLATE.md`.

The promotion record must name:
- the source idea or experiment
- what the idea becomes
- the required next action
- who approved it

A promotion record without an approval field completed is PROPOSED, not APPROVED.

---

## Self-promotion is not allowed

An agent may not approve its own promoted idea if the idea constitutes a substantive deliverable.

Substantive means: it changes HPOM gates, alters shared state, modifies task structure, or introduces a new MAP-level process.

Route it to the operator or to the other core agent for review.

---

## Promotion does not mean implementation

Promotion creates a task or decision record. It does not authorize immediate implementation.

The promoted task enters HPOM at PROPOSED or READY status. It is subject to normal claiming, review, and release gates from that point.
