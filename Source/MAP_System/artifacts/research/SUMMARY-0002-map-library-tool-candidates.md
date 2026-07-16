# Research Summary

Summary ID: SUMMARY-0002
Related brief: BRIEF-0002
Related claim matrix: folded into SOURCE-MAP-0002 for TASK-154 scope
Related assumption register: folded into this summary's open questions
Owner: codex-lab-mozu
Date: 2026-07-13
Status: FINAL

## Question

Which external Library/memory/collaboration/tooling candidates are worth
studying for MAP's future Library layer, outcome gates, and worktree/locking
lessons, and what must be measured before any adoption decision?

## Answer

No external candidate should be adopted from this pass. The current evidence
supports studying specific patterns and running MAP's Library viability
measurement plan first.

Candidate conclusions:

| Candidate | TASK-154 evaluation | No-adoption reason |
|---|---|---|
| `iurykrieger/claude-bedrock` | Best direct blueprint for Obsidian/wikilink librarian mechanics: entity-typed Markdown vault, bidirectional links, ingestion, healthcheck/compress/sync loops. | Plugin/runtime fit, error-reporting behavior, and stale-summary behavior must be tested on MAP content first. |
| `ccf/agentcairn` | Strongest memory-layer reference for local-first, inspectable, cross-agent memory with Markdown source of truth, rebuildable index, redaction, provenance, and project-scoped recall. | Automatic memory recall can conflict with MAP's bounded Context System unless measured and gated. |
| Knowledge-graph-driver-RAG hop-limit/token-budget pattern | Keep the pattern: graph traversal needs hard hop limits and token budget caps. | The current repo was not verified during TASK-154; use the pattern, not the repo claim, until rechecked. |
| `WenyuChiou/agent-collab-skills` | Useful reference for task splitting, reconciliation, shared memory, debate, and especially acceptance-gate artifacts. | MAP already has HPOM/review/validator gates; compare mechanics rather than duplicate or replace them. |
| `milisp/codexia` | Useful control-plane reference for worktree management, scheduling, remote/headless API, lifecycle/approval/git/filesystem routes, and process isolation. | It is a broad workstation/control-plane with security and license implications, not a Library layer. |

The measurement prerequisite is `MAP_System/artifacts/audits/map-library-viability-measurement.md`.
Before any Library/tool adoption task, MAP must measure compression ratio,
detail-needed rate, file churn, staleness invalidation, and missed-detail
incidents on real MAP docs.

## Confidence

- [ ] HIGH — answer rests on PRIMARY sources, no unresolved contradictions
- [x] MEDIUM — answer rests mainly on SECONDARY sources or has open,
      non-blocking caveats
- [ ] LOW — answer rests on COMMUNITY/UNVERIFIED sources or unresolved
      contradictions; state explicitly what would raise confidence

Confidence is medium because four candidate repository pages were checked
directly on 2026-07-13, but the Knowledge-graph-driver-RAG repo itself was not
verified online and all tool benefit claims still require local MAP
measurement.

## Confidence decays after

Re-verify before reuse if this summary is more than one active project cycle
old, or before any task proposes installing, integrating, or depending on one
of the candidate tools.

## Open questions

- Can `claude-bedrock` or `agentcairn` preserve MAP's rule that durable MAP
  files, not memory recall, remain source of truth?
- What is the stale-summary/read rate when summaries are generated from real
  MAP docs and then invalidated by normal task churn?
- Does `agent-collab-skills` acceptance-gate structure catch defects MAP's
  current validators/reviews miss, or only duplicate existing HPOM gates?
- Which exact hop-limit/token-budget settings work on MAP's docs?
- What security review is required before any control-plane tool with remote
  filesystem/git/terminal surfaces can influence MAP?

-

## Downstream effect

- [ ] Feeds a decision — link the new/updated `DEC-NNN` in
      `shared/decisions.md`: NONE
- [x] Feeds a task — link the task and confirm this summary is listed in
      its `input_paths`: TASK-154 output; future adoption tasks must cite this
      summary and the Library viability measurement plan.
- [ ] Informational only — no immediate downstream action

## Notes

- This summary intentionally makes no adoption decision.
- Future adoption requires a separate HPOM task, current source refresh,
  security review where applicable, and measurement against real MAP traffic.
