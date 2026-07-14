# Research Brief

Brief ID: BRIEF-0002
Project: MAP_System
Related task: TASK-154
Requested by: codex-lab-mozu
Owner: codex-lab-mozu
Date opened: 2026-07-13
Status: FINAL

## Research question

Which external Library/memory/collaboration/tooling candidates are worth
studying for MAP's future Library layer, outcome gates, and worktree/locking
lessons, and what must be measured before any adoption decision?

## Why this matters

MAP 6.13 explicitly requires a Research System pass before adopting any
Library/tool layer. The knowledge layer is high-risk because stale summaries,
lossy retrieval, or opaque memory can become false project truth.

## What would count as an answer

A candidate-by-candidate evaluation that identifies:

- what each tool or pattern appears to provide;
- whether it is a direct blueprint, pattern reference, or poor fit;
- what MAP must measure before adoption;
- what claims remain unverified or time-sensitive.

## Time sensitivity

- [ ] Stable (math, established protocol, historical fact)
- [x] Time-sensitive (pricing, API version, library behavior, security
      advisory, anything that can change out from under the answer)

If time-sensitive, state the expected re-verify interval:

Re-check repository status, README claims, release state, and license before
any implementation/adoption task. Treat this summary as stale after one active
project cycle or any major candidate release.

## Scope boundary

In scope: `iurykrieger/claude-bedrock`, `ccf/agentcairn`, the
Knowledge-graph-driver-RAG hop-limit/token-budget pattern,
`WenyuChiou/agent-collab-skills`, and `milisp/codexia`.

Out of scope: installing any tool, cloning any repo, adopting a dependency,
or making a binding architecture decision.

## Linked artifacts

- Source Map: `MAP_System/artifacts/research/SOURCE-MAP-0002-map-library-tool-candidates.md`
- Source Evaluation: folded into Source Map for TASK-154 scope
- Claim Evidence Matrix: folded into Source Map for TASK-154 scope
- Assumption Register: folded into Research Summary open questions
- Research Summary: `MAP_System/artifacts/research/SUMMARY-0002-map-library-tool-candidates.md`

## Notes

- TASK-154 deliberately declares only Brief, Source Map, and Summary outputs.
  Detailed source evaluation and claim matrix should be split into a larger
  research task if adoption becomes likely.
