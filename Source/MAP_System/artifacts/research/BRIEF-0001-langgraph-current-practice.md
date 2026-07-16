# Research Brief

Brief ID: BRIEF-0001
Project: MAP_System
Related task: TASK-145
Requested by: command-center (hcom broadcast #25059, full MAP renewal cycle)
Owner: claude-lab-magi
Date opened: 2026-07-04
Status: CLOSED

## Research question

Is MAP's current LangGraph usage (`MAP_System/graph/runner.py`, installed
`langgraph==1.2.7`) aligned with current upstream LangGraph practice for the
patterns it actually uses — `StateGraph`, `Command`, `interrupt`, conditional
routing, and human-in-the-loop approval gates — or has upstream guidance
moved in a direction MAP has not adopted (e.g. persistence/checkpointer
requirements for `interrupt`, deprecated APIs still in use, a now-recommended
pattern MAP is missing)?

## Why this matters

The operator asked for a full MAP renewal pass that explicitly names
"LangGraph use" as something to check against what we've learned, and asked
for research where agent training knowledge might be stale. `runner.py` is
the core dependency-routing engine for every task in MAP; if it relies on a
deprecated or soon-to-be-removed API shape, or is missing a now-standard
safety pattern (e.g. checkpointer for `interrupt`/resume correctness), that
is a real risk to the whole task pipeline, not a cosmetic gap.

## What would count as an answer

A statement, per checked pattern (StateGraph/Command/interrupt usage,
conditional edges, checkpointer/persistence), of: still-current /
deprecated-but-working / deprecated-and-risky / missing-recommended-pattern,
each with the source that supports it and a confidence level.

## Time sensitivity

- [ ] Stable (math, established protocol, historical fact)
- [x] Time-sensitive (pricing, API version, library behavior, security
      advisory, anything that can change out from under the answer)

Time-sensitive: LangGraph is an actively developed library; re-verify before
reuse if this summary is more than one MAP renewal cycle old, or immediately
if `requirements.txt` bumps the pinned `langgraph` version.

## Scope boundary

In scope: the specific LangGraph API surface `runner.py` and `agent_loop.py`
actually call. Out of scope: a general LangGraph tutorial/survey, other
LangChain-ecosystem packages not imported by MAP, and any recommendation to
switch orchestration frameworks entirely (that would be an ARCHITECTURE-class
decision requiring its own brief, not an outcome of a usage-currency check).
Also out of scope: applying any fix directly — this brief hands findings to
TASK-144 (codex-lab-veto, structural assessment/cleanup coordinator) as an
input packet.

## Linked artifacts

- Source Map: `MAP_System/artifacts/research/SOURCE-MAP-0001-langgraph-current-practice.md`
- Source Evaluation: `MAP_System/artifacts/research/SOURCE-EVAL-0001-langgraph-current-practice.md`
- Claim Evidence Matrix: `MAP_System/artifacts/research/CLAIM-MATRIX-0001-langgraph-current-practice.md`
- Assumption Register: `MAP_System/artifacts/research/ASSUMPTIONS-0001-langgraph-current-practice.md`
- Research Summary: `MAP_System/artifacts/research/SUMMARY-0001-langgraph-current-practice.md`

## Notes

- This is the first real exercise of the Research System (previously
  specification-only per DEC-027 / TASK-129/130) — DEC-027 named exactly
  this trigger condition: a genuine external, current-practice technology
  question, not an internal implementation detail knowable from the repo
  alone.
