# Working-Backwards Brief: MAP's First Real Proving Workflow

- Author: gune (orchestrator), 2026-07-15
- Purpose: resolve the standing OPEN question ("first real workflow target:
  writing / software / research / PM?" — `shared/unresolved-questions.md`,
  `improvement-backlog.md`) using Amazon's working-backwards method: start from
  a customer and a concrete deliverable, then work back to what MAP must run.
- Source: INS-0023 (MAP builds inward without a proving workflow); E/I
  benchmark 2026-07-15.
- Status: DECIDED — operator selected **Software delivery** (2026-07-15),
  recorded as DEC-028. First slice: ProjectUpdater JSON import (IDEA-0015).

## Why this matters

MAP is architecturally ahead of the field on durability + mechanical gates
(INS-0022), but every recent task (197–204) is internal infrastructure. Without
a real deliverable flowing through the gates on a cadence, MAP keeps proving
itself *to itself*. Working-backwards fixes the direction: pick one customer +
one recurring deliverable, and let MAP's gates produce a visible quality win.

## The test each candidate must pass

1. **Real customer** — a named person who wants the output (not MAP itself).
2. **Objective-enough gates** — acceptance criteria MAP can actually check.
3. **Bounded + repeatable** — a slice shippable in days, repeatable on a cadence.
4. **Exercises the differentiator** — durable state + review/release gates add
   visible value, not ceremony.
5. **Fits the two core agents** — Codex (implementation) + Claude (synthesis/review).

## Candidates (each a compact PR/FAQ)

### A. Software delivery — "MAP ships and maintains a real tool"
- **Press release:** *"A solo builder describes a small tool; MAP's agent team
  designs, implements, reviews, and releases it — with every change gated,
  owned, and reversible."* First slice: a bounded upgrade to an existing
  workspace tool (e.g. ProjectUpdater v2) or one new small utility.
- **FAQ:** Customer = the tool's end user (and the operator). Gates = tests +
  code review + release checklist (already MAP-native). Fit = Codex-led,
  Claude-reviewed. Strongest *objective* gates; MAP already did a one-off of
  this (ProjectUpdater TASK-123–125) — this makes it a **standing** workflow.
- **Risk:** scope creep; needs a real backlog of user-facing features.

### B. Research/intelligence product — "MAP Intelligence Brief on a cadence"
- **Press release:** *"Every week MAP delivers a sourced, current briefing on a
  question the operator cares about — competitive moves, tech shifts, decisions
  to make — synthesized and peer-reviewed by the agent team."* First slice:
  productize today's E/I benchmark into a repeatable brief format.
- **FAQ:** Customer = the operator/decision-maker. Gates = source validation
  (Research system DEC-015) + review + emergence capture. Fit = Claude-led
  synthesis, cross-reviewed. **Lowest-risk, fastest-to-prove** (the pipeline
  already worked today) and it compounds — each brief sharpens MAP.
- **Risk:** value depends on question quality; softer acceptance criteria than software.

### C. Creative/long-form writing — "MAP runs Pathwell"
- **Press release:** *"MAP takes the Pathwell story project from outline to
  reviewed chapters, with continuity, voice, and canon enforced by durable
  state and peer review."*
- **FAQ:** Customer = the reader (and operator). Gates = continuity/canon
  checks + review; but quality is **subjective** — weakest fit for mechanical
  gates. Fit = Claude-led. Real and already in-workspace.
- **Risk:** subjective acceptance; hardest to prove MAP's gates add quality.

## Recommendation

**Start with B (Intelligence Brief) as the proving workflow, with A (software)
as the immediate second track.**

Reasoning: B is the smallest end-to-end slice that already demonstrably works
(today's benchmark ran research → capture → helper authoring → review → release
cleanly), it compounds (every brief improves MAP's own roadmap), and it needs
no new domain scaffolding. It de-risks the *process* first. Then A adds the
objective-gate rigor on a real code deliverable once the cadence is proven.
C (Pathwell) is real but its subjective gates make it the weakest *first* proof.

## Proposed first move (reversible, bounded)

If B: create a task to define the "MAP Intelligence Brief" format + cadence
(template, source-validation checklist, review/release path, one pilot brief),
delegated to a helper, reviewed by a core agent. One pilot proves the loop; the
operator can redirect after seeing it.

## The decision that's genuinely the operator's

Which proving workflow (or ordering) MAP commits to is a project-direction call.
This brief is the legwork + a recommendation; the pick is the operator's.
