# MAP Library Viability Measurement — Results (2026-07-14)

Task: TASK-174
Owner: claude-lab-zera
Plan: `map-library-viability-measurement.md` (TASK-154)
Tool: `scripts/librarian.py measure`

## Purpose

`map-library-viability-measurement.md` named this measurement as the
Gap-Register's #1-priority, never-run prerequisite before building or
adopting any Library layer. This document runs it for real, against real
MAP files, and reports the honest result — including where the measurement
itself is inconclusive.

## Compression Ratio (Real Measurement)

Ran against all 16 root system/policy docs
(`*_SYSTEM.md`, `AGENT_PERMISSION_LEVELS.md`, `DECISION_CLASSES.md`,
`DESTRUCTIVE_ACTION_POLICY.md`, `NEW_PROJECT_WIZARD.md`) using the
cheapest possible summarizer (headings + first body paragraph, no LLM):

| Metric | Value |
|---|---|
| Files measured | 16 |
| Median compression ratio | **22.65x** |
| P90 compression ratio | 28.94x |
| Worst-case compression ratio | 12.6x (`ORCHESTRATION_ENTRYPOINT_SYSTEM.md`, shortest doc) |

**This number is not evidence the Library layer should be built.** It is a
floor measurement using the cheapest possible extractive strategy (headings
+ first paragraph only, no body content). The plan's own adoption threshold
requires "low missed-detail rate" alongside compression — a summary this
aggressive almost certainly has a high detail-needed rate, since it
discards every procedural rule, table, and cross-reference in the body.
This measurement establishes that naive extraction compresses well; it does
NOT establish that a naive extractive summary is a viable Library-layer
summary. That question requires the detail-needed-rate measurement below,
which is still unmeasured.

## File Churn (Measurement Inconclusive — Real Limitation Found)

Ran `git log --since="30 days ago"` against the same 16 files:

| Metric | Value |
|---|---|
| Files with any commit in the window | **0 of 16** |

This is not a "MAP docs don't change" finding. It reflects a repo-level
fact discovered while running this measurement: **the last commit in this
repository is `92b186d` (TASK-100), and every task from TASK-101 onward —
this entire session's work, roughly 74 tasks — is uncommitted in the
working tree.** `git log`-based churn measurement is unusable until a
baseline commit lands; it currently measures "time since last commit,"
not "how often these files actually change." Flagging this as a
housekeeping item worth raising separately (see Notes below) — it is a
real gap the measurement surfaced, not a Library-layer question.

## Detail-Needed Rate — Not Measured

Per the plan, this requires "run normal MAP tasks/reviews for one cycle
using summaries as optional first-read context" and logging whether
agents opened full sources and why. That requires live usage over time,
not a one-shot script run. **Still the single largest gap** between "we
have a compression number" and "we know if a Library layer would help."
Not fabricated here.

## Staleness Invalidation — Partially Addressed By Design, Not Measured

`librarian.py` does not yet implement staleness invalidation (no stored
content-hash-vs-current-hash comparison). This task built wikilink
resolution/validation and measurement tooling, not the full staleness
mechanism — that remains a distinct follow-on if the Library layer
proceeds past this measurement stage.

## What This Measurement Actually Establishes

1. **Compression is achievable** at the ratios the 6.13 research assumed
   (10x+), using the cheapest possible method — this is a genuinely
   positive floor signal.
2. **The real blocker remains detail-needed rate**, which cannot be
   measured without a live usage cycle. This is unchanged from the
   Gap-Register's original assessment; this task moves the compression
   half of the measurement from "assumed" to "measured," but not the
   detail-needed half.
3. **Churn measurement needs a committed baseline first** — a repo-level
   finding independent of the Library-layer question.

## Recommendation

Do not proceed to building the full Library layer yet. The adoption
threshold requires low missed-detail rate and zero stale-reads for
high-authority work — neither is measurable without either (a) a
detail-needed-rate tracking mechanism wired into normal task/review work,
or (b) accepting a smaller controlled pilot (e.g. summarize 3-5 docs, use
them for a handful of real tasks, and manually log every full-source
open). Recommend (b) as the next bounded step if the operator wants to
keep pushing this forward, since (a) requires infrastructure this task
did not build.

## What Was Built Instead (Real, Not Simulated)

Per the operator's "implement, don't just design" directive, this task
also shipped the first real librarian-agent code rather than stopping at
another measurement report:

- `scripts/librarian.py`: wikilink resolution (with ambiguous-stem
  disambiguation — e.g. the 28 different `README.md` files in this repo
  all shared the bare stem `README` until this task's own validator
  caught it), validation (broken/ambiguous link detection), backlink
  index construction, and this measurement runner.
- **118 real wikilinks added** across the 16 root system/policy
  docs' Related-Files sections — additive (original backtick paths
  preserved) and idempotent (re-running does not duplicate links).
  Zero broken or ambiguous links per `librarian.py validate`.
- A real backlink index now exists across 38 files (run
  `python3 MAP_System/scripts/librarian.py backlinks` for the live graph).

## Related Files

- `map-library-viability-measurement.md` [[map-library-viability-measurement]] — the measurement plan this executes
- `SUMMARY-0002-map-library-tool-candidates.md` [[SUMMARY-0002-map-library-tool-candidates]] — prior tool research
- `scripts/librarian.py` — the tool that produced these numbers (not
  wikilinkable yet: `librarian.py`'s current scope only indexes `.md`
  files, so `.py` script references stay as plain paths — a known
  limitation, not a bug, until/unless script cross-referencing is wanted)
- `tests/test_librarian.py` — its test suite
