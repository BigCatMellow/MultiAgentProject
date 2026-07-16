# Source Map

Source Map ID: SOURCE-MAP-0002
Related brief: BRIEF-0002
Owner: codex-lab-mozu
Date: 2026-07-13
Status: FINAL

List candidate sources before reading them in depth, so coverage is visible
before effort is spent. Add rows as sources are found; do not remove rows
for sources that turned out unhelpful - mark them instead.

## Candidate sources

| # | Source | Type | Locator | Why relevant | Status |
|---|---|---|---|---|---|
| 1 | MAP 6.13 master implementation plan | local planning artifact | `MAP_System/artifacts/planning/map-613-master-implementation-plan.md`, Wave 6 | Defines TASK-154 required candidates and no-adoption constraint. | used |
| 2 | MAP Repo Review List | local research list | `Guidelines/6.13/MAP-Repo-Review-List.md` | Lists the Library/memory/collaboration/worktree candidates and prior read order. | used |
| 3 | MAP Tool-Evaluation Appendix | local research appendix | `Guidelines/6.13/files3/MAP-Tool-Evaluation-Appendix.md` | Gives prior tool-evaluation framing and dependency discipline. | used |
| 4 | `iurykrieger/claude-bedrock` GitHub page | repo / primary candidate source | `https://github.com/iurykrieger/claude-bedrock`, retrieved 2026-07-13 | Current README describes Obsidian/Claude Code knowledge graph mechanics. | used |
| 5 | `ccf/agentcairn` GitHub page | repo / primary candidate source | `https://github.com/ccf/agentcairn`, retrieved 2026-07-13 | Current README describes local-first cross-agent memory, Obsidian vault, provenance, and recall. | used |
| 6 | `WenyuChiou/agent-collab-skills` GitHub page | repo / primary candidate source | `https://github.com/WenyuChiou/agent-collab-skills`, retrieved 2026-07-13 | Current README describes task splitter, shared memory, reconciler, and acceptance gate. | used |
| 7 | `milisp/codexia` GitHub page | repo / primary candidate source | `https://github.com/milisp/codexia`, retrieved 2026-07-13 | Current README describes worktree management, scheduling, remote control, APIs, and process isolation. | used |
| 8 | `Roshan02-CIT/Knowledge-graph-driver-rag-for-agentic-coding-tools` | local candidate listing / unverified current repo | `Guidelines/6.13/MAP-Repo-Review-List.md` | Required TASK-154 pattern: graph traversal with hop limit and token budget cap. | used with caveat |

## Coverage check

- [x] At least one PRIMARY-candidate source identified (see
      `SOURCE_EVALUATION_TEMPLATE.md` ratings)
- [x] Sources span more than one independent origin (not all mirrors of the
      same upstream text)
- [x] Any known authoritative source (official docs, spec, source code) is
      included or explicitly noted as unavailable

## Source evaluation notes

| Source | Rating | Notes |
|---|---|---|
| MAP 6.13 plan | PRIMARY | Canonical for TASK-154 scope. |
| MAP Repo Review List | SECONDARY | Local prior research list; useful but explicitly says repo claims require current verification. |
| MAP Tool-Evaluation Appendix | SECONDARY | Local prior analysis; useful for MAP-specific fit, not a current repo fact source. |
| `claude-bedrock` GitHub page | PRIMARY for README claims | Current GitHub page reports MIT license, plugin/skills, Obsidian vault, bidirectional links, external ingestion, healthcheck/compress/sync, and opt-out error reporting. |
| `agentcairn` GitHub page | PRIMARY for README claims | Current GitHub page reports Apache-2.0 license, Markdown/Obsidian source of truth, disposable DuckDB index, redaction, provenance/currency, multi-agent support, and recall behavior. |
| `agent-collab-skills` GitHub page | PRIMARY for README claims | Current GitHub page reports MIT license, task splitter, output reconciler, debate, shared memory, acceptance gate, and `.coord/` artifacts. |
| `codexia` GitHub page | PRIMARY for README claims | Current GitHub page reports AGPL-3.0/commercial license, task scheduler, git worktree management, remote/headless API, process isolation, and permission controls. |
| Knowledge-graph-driver-RAG listing | UNVERIFIED for current repo; SECONDARY for local pattern | Web search/open did not verify the repo during TASK-154. Use only the hop-limit/token-budget pattern from local MAP materials until re-verified. |

## Candidate evaluation notes

### `iurykrieger/claude-bedrock`

Fit: direct librarian-bot blueprint for Obsidian/wikilink mechanics.

Useful ideas:

- entity-typed Markdown vault;
- bidirectional wikilinks;
- source ingestion;
- healthcheck/compress/sync loops;
- single write/preserve skill pattern.

MAP caveats:

- Claude Code plugin shape may not map to hcom/core-agent ownership directly;
- opt-out error reporting must be reviewed before use with MAP content;
- adoption must wait for Library viability metrics.

### `ccf/agentcairn`

Fit: strong memory-layer reference for local-first, cross-agent, inspectable
memory.

Useful ideas:

- Markdown vault as source of truth;
- rebuildable DuckDB index as cache;
- redaction before writes;
- provenance/currency framing;
- automatic recall scoped to current project.

MAP caveats:

- automatic recall must not override MAP context packets or durable task state;
- memory injection should be framed as untrusted historical evidence;
- measure stale recall and integration cost before adoption.

### Knowledge-graph-driver-RAG hop-limit/token-budget pattern

Fit: pattern reference, not verified current dependency.

Useful idea:

- graph traversal should have a hard hop limit and token budget cap so
  retrieval cannot become an unbounded context dump.

MAP caveats:

- repo itself was not currently verified during TASK-154;
- implement the pattern only after testing it on MAP docs;
- no adoption decision should cite this as a trusted repo without re-checking.

### `WenyuChiou/agent-collab-skills`

Fit: collaboration workflow reference, especially acceptance-gate mechanics.

Useful ideas:

- task splitter and output reconciler as explicit artifacts;
- acceptance gate before merge;
- shared memory and debate as bounded supporting skills;
- `.coord/` trace artifacts.

MAP caveats:

- MAP already has HPOM, review gates, and validators; do not duplicate them;
- acceptance gate should be compared to validator/halt behavior, not adopted
  wholesale;
- helper authority boundaries must remain MAP's.

### `milisp/codexia`

Fit: control-plane/workstation reference for worktree and remote-control risks.

Useful ideas:

- git worktree management in an agent workstation;
- scheduler and remote control surface;
- explicit API routes for agent lifecycle, approvals, filesystem, git, and
  terminal;
- process isolation and configurable permissions.

MAP caveats:

- license and control-plane write capabilities require careful review;
- remote/headless API is a security/control-surface risk for MAP;
- use as a design/risk reference for CommandCenterUI and git locking, not as a
  replacement for MAP's state model.

## Low-confidence claims

- Current status of `Roshan02-CIT/Knowledge-graph-driver-rag-for-agentic-coding-tools`
  was not verified online during TASK-154.
- Token/compression/retrieval benefit claims from any candidate remain
  untrusted until measured on real MAP traffic.

## Contradictions

No direct contradictions were found among used sources. The main tension is
architectural: external memory tools often want to inject recall automatically,
while MAP's Context System requires bounded, purpose-built context packets.

## Notes

- This Source Map intentionally combines source evaluation notes because
  TASK-154 declared only Brief, Source Map, and Summary research outputs.
