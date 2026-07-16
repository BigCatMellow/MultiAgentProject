<!-- hpom: file: research/README.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-103 build -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Research System — Quick Start

See `MAP_System/RESEARCH_SYSTEM.md` for the full system definition,
principles, and rules. This file is the working quick-start for producing a
research artifact set.

## When to open a research task

Open one when a task or decision depends on a claim that is not already
verified project truth: an external API's current behavior, a library's
license terms, a security advisory, a pricing model, or any fact an agent
would otherwise state from memory without a source.

Do not open one for questions answerable by reading this repository's own
canonical files (`shared/`, task records, decisions) — that is a normal
read, not research.

## Steps

1. Write a Research Question. Make it specific and answerable.
2. Copy `MAP_System/templates/research/RESEARCH_BRIEF_TEMPLATE.md` to
   `MAP_System/artifacts/research/BRIEF-NNNN-<slug>.md` (or the project's
   `research/briefs/` folder) and fill it in.
3. Copy `SOURCE_MAP_TEMPLATE.md` to
   `.../SOURCE-MAP-NNNN-<slug>.md`, list candidate sources.
4. Copy `SOURCE_EVALUATION_TEMPLATE.md`, rate each source that was actually
   used (`PRIMARY`/`SECONDARY`/`COMMUNITY`/`UNVERIFIED`/`STALE`).
5. Copy `CLAIM_EVIDENCE_MATRIX_TEMPLATE.md`, extract one claim per row, tie
   each to a source and locator.
6. Copy `ASSUMPTION_REGISTER_TEMPLATE.md` for anything used without a
   source.
7. Copy `RESEARCH_SUMMARY_TEMPLATE.md`, write the final operator-facing
   answer, confidence, and open questions.
8. If the summary changes project truth: add a `DEC-NNN` entry to
   `MAP_System/shared/decisions.md` that links the summary path.
9. If the summary unblocks implementation: create or update a task with the
   summary path in `input_paths`.
10. Log a `PROGRESS` event when starting and a `SUBMISSION` event when the
    summary is complete, in `MAP_System/events/events.jsonl`.

## Numbering

Use a shared 4-digit sequence per artifact type, e.g. `BRIEF-0001`,
`SOURCE-MAP-0001`, `CLAIM-MATRIX-0001`, `ASSUMPTIONS-0001`,
`SUMMARY-0001`. Reuse the same `NNNN` suffix across all five files for one
research question so they stay linkable, e.g. all filed under `-0001-`.

## Folder layout

```
MAP_System/
  artifacts/research/        ← MAP-system-level research artifacts
  templates/research/        ← the six templates, copy don't edit in place
Projects/<PROJECT_NAME>/
  research/
    briefs/
    sources/
    evidence/
    assumptions/
    summaries/
```

## What this does not replace

- It does not replace `shared/decisions.md` — conclusions still land there.
- It does not replace Emergence — a passing hunch is still an `INS-NNNN`,
  not a Research Brief, until it is specific enough to investigate.
- It does not replace task review gates — a Research Summary is input to a
  task, not itself an implementation change.
