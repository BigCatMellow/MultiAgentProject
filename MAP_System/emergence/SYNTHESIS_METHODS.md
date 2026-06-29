# Synthesis Methods

## What synthesis is

Synthesis combines two or more separate things into a new idea that was not in any of the original pieces.

The paint analogy:
```
blue + yellow = green
```

Green was not given. It was made possible by the relationship between the given materials.

Synthesis in MAP asks:
```
What new thing does the combination of these existing things make possible?
```

---

## When to synthesize

Synthesize when you notice:

- Two separate tasks that solve the same underlying problem differently
- A repeated fix that suggests a missing abstraction
- A local solution that could become a generic reusable pattern
- A constraint in one area that removes a problem in another
- A template that covers three existing formats if generalized slightly
- Two insights that point at the same root cause

Do not synthesize from single weak observations. Synthesis requires at least two solid inputs.

---

## Synthesis method: Structural overlap

Find two things that have the same structure.

Example:
```
READY gate requires: inputs, pass criteria, fail criteria, evidence, next state, owner
REVIEW gate requires: inputs, pass criteria, fail criteria, evidence, next state, owner
RELEASE gate requires: inputs, pass criteria, fail criteria, evidence, next state, owner

→ Synthesis: MAP needs a generic GATE_SCHEMA.
```

Use this when: repeated structures appear across tasks, scripts, or artifacts.

---

## Synthesis method: Tension resolution

Find two things that are in tension and look for what resolves both.

Example:
```
Agents need creative freedom to notice useful possibilities.
HPOM needs controlled execution to prevent scope creep.

→ Synthesis: A separate emergence layer that captures ideas without acting on them.
```

Use this when: two good requirements pull in opposite directions.

---

## Synthesis method: Gap bridging

Find what is missing between two existing capabilities.

Example:
```
MAP has task validation gates.
MAP has release artifacts.
There is no lightweight path from a half-formed idea to a formal task.

→ Synthesis: An idea card and experiment record that bridge informal discovery to formal HPOM tasks.
```

Use this when: something is missing that would connect two existing capabilities.

---

## Synthesis method: Pattern abstraction

Find a repeated specific case and name the general form.

Example:
```
Pathwell has: chapter-level review, scene-level notes, character arc tracking.
These are all: artifact → review → status update cycles.

→ Synthesis: A generic MAP artifact review cycle, not just a code review cycle.
```

Use this when: a project-specific pattern could become a reusable MAP pattern.

---

## What to do with a synthesis

1. Write a synthesis note using `templates/SYNTHESIS_NOTE_TEMPLATE.md`.
2. Name the new combination clearly.
3. State what it makes possible.
4. State the smallest safe experiment.
5. Route it: park, test, or create an idea card.

Do not silently act on a synthesis. Capture it first.

---

## Synthesis quality test

A synthesis is worth preserving if:

- It names something that did not have a name before.
- It reduces duplication or resolves a known tension.
- It is specific enough to test.
- It is connected to real existing evidence.

A synthesis should be parked or dropped if:

- It is only interesting but not actionable.
- It requires evidence that does not yet exist.
- It would require major decisions before it could be tested.
- It generalizes too far too quickly.
