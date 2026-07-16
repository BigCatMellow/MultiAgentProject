<!-- hpom: file: CONTEXT_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-107 build, Guidelines/MAP_repo_systems_gap_review.md -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Context System

Status: active
Decision: DEC-017
Owner: command-center
Built by: TASK-107

## What this is

`notes/context-routing-guide.md` already tells an agent which files to read
together for common situations. This file formalizes the rules around that
guide: what a context packet actually contains, what is required vs.
optional vs. forbidden, how staleness is handled, and how token budget and
compression are governed. It does not replace the routing guide's
situational table — it governs the packet the routing guide produces.

## Core principle

```
Every task should have a context packet, not a context dump.
```

A context packet is a bounded, purpose-built set of references for one unit
of work. It is not "everything that might be relevant" — that is a dump,
and dumps cost tokens, hide the signal, and go stale silently.

## Context packet format

A context packet has four parts. Use
`templates/CONTEXT_PACKET_TEMPLATE.md` to assemble one for non-trivial
tasks; trivial tasks may assemble it informally but should still be able to
name these four parts if asked.

| Part | Contents |
|---|---|
| Anchor | The task/decision/question this packet serves — one ID, one line |
| Required | Files that must be read before acting (see table below) |
| Optional | Files to follow only if a listed trigger condition is met |
| Excluded | Files deliberately not loaded, and why (prevents silent over-reading later) |

## Required context by task type

| Task type | Required minimum |
|---|---|
| Implementation | `AGENTS.md`, `shared/current-state.md`, task file, task `input_paths` |
| Review | `notes/review-guide.md`, task file, `acceptance_criteria`, `output_paths` |
| Architecture / system build (like this one) | `shared/decisions.md`, `shared/hpom.md`, the gap or brief that motivated it, any system this one must cross-link |
| Research | `RESEARCH_SYSTEM.md`, the Research Brief, prior Research Summaries on the same question if any exist |
| Repair | `SELF_REPAIR_SYSTEM.md`, `shared/current-state.md`, `shared/improvement-backlog.md`, the failing validator's output |
| Decision | `shared/decisions.md`, `shared/unresolved-questions.md`, `shared/constraints.md` |

This table is a floor, not a ceiling — `notes/context-routing-guide.md`'s
"Common Situations" section gives the fuller per-situation reading order.

## Optional context

Optional context is anything gated by a trigger, not read by default:

- Historical artifacts (`artifacts/`, `archive/`) — only when a current file
  says it is superseded, or provenance is actually in question.
- Full event log (`events/events.jsonl`) — only the tail relevant to the
  task, not the full history, unless reconstructing timeline is the task.
- Other agents' full session transcripts — only when a handoff or
  STATE_SNAPSHOT points to a specific one as unresolved.
- Project-level docs (`Projects/<PROJECT_NAME>/`) — only when the task is
  scoped to that project.

## Forbidden context loading

Do not load, by default:

- The entire Markdown tree (`shared/memory-map.md` already says this).
- `archive/`, `.venv/`, `.locks/`, `exports/`, `snapshots/` (per
  `AGENTS.md` routing — non-primary unless a task explicitly asks for
  them).
- Another core agent's in-progress owned output paths, unless reviewing or
  explicitly handed off — reading is fine, but do not fold their draft
  content into your own packet as if it were settled.
- Unsourced claims as if they were context — an unverified fact belongs in
  a Research Brief/Assumption Register (`RESEARCH_SYSTEM.md`), not silently
  in a context packet as background truth.

## Stale context handling

A context packet can go stale the same way any file can. Treat stale
context as a `DRIFT`-severity finding under
`SELF_REPAIR_SYSTEM.md`, not something to silently work around:

- If a file in the packet is marked superseded, follow the supersession
  chain before using it.
- If `shared/current-state.md` disagrees with an artifact in the packet,
  `current-state.md` wins per the routing guide's conflict order, and the
  disagreement should be logged as a repair if it recurs.
- If a STATE_SNAPSHOT or handoff is older than the current session's
  starting state, treat it as orientation only, not authoritative —
  `AGENTS.md`- and `shared/memory-map.md`-listed canonical files remain the
  source of truth.

## Token-budget rules

- Read the smallest useful set first (per the routing guide's default
  stack); expand only when something is unclear, per that guide's "When To
  Follow More Links" section.
- Do not re-read a file already in context this session merely to double
  check it — trust what was already read unless the file could plausibly
  have changed since.
- For large historical artifacts, prefer reading a summary or the relevant
  section over the full file when a summary already exists
  (`notes/brain-compaction-guide.md` compaction summaries, Research
  Summaries, Health Check Reports).
- When a task's context need is genuinely large (e.g., full-repo audits
  like the gap review), that is itself a signal to delegate a scoped
  research or review pass rather than loading everything into one agent's
  working context.

## Local-summarizer role

Per `shared/hpom.md` Tier 3, local assistants may compress context — they
may not decide what is canonical:

- A local model may produce a first-pass summary of a large artifact
  (event digest, current-state summary, a long historical file) for a core
  agent to verify before treating it as the packet's Required content.
- A local model may classify which candidate files look relevant to a
  question, narrowing a Source Map (see `RESEARCH_SYSTEM.md`) or a
  candidate reading list.
- A local model may not resolve a stale-vs-current conflict, or decide
  that a file is safe to exclude from a packet for a `STRUCTURAL`-risk
  task — that judgment stays with a core agent.

## Context compression rules

- Compress forward, don't delete backward: when a context packet's source
  material is compacted (per `notes/brain-compaction-guide.md`), the
  compacted summary replaces the packet's Required entry, but the raw
  material stays retrievable in `archive/`.
- A compaction summary used inside a context packet must name what it
  compacted (source paths), so a future reader can expand back to raw
  history if the summary turns out insufficient.
- Do not compress a context packet by dropping the Excluded section —
  knowing what was deliberately left out is as valuable as knowing what was
  included, especially for STRUCTURAL-risk work.

## Relationship to other systems

```
Memory defines what is canonical.
Context loads the right canonical slice for one task.
Research feeds Context verified facts instead of raw sourcing.
Emergence feeds Context which insights are worth carrying forward.
Self-Repair treats stale or conflicting context as a repair target.
HPOM bounds who may compress, summarize, or decide what belongs in context.
```

- **Memory** (`shared/memory-map.md`): Context System governs how a packet
  is assembled from memory-map's canonical list; it does not replace the
  map itself.
- **Research System**: a context packet should carry a Research Summary's
  conclusion, not the raw Source Map or Claim Evidence Matrix — those stay
  linked, not inlined, to keep the packet bounded.
- **Self-Repair System**: a context packet built on stale or contradictory
  files is itself a `DRIFT` finding; file a Repair Record if this recurs
  for the same file.
- **Emergence System**: an `INS-NNNN` insight about "we keep re-reading the
  same five files for this situation" is exactly the kind of observation
  that should update `notes/context-routing-guide.md`'s situational table.

## Related files

- `notes/context-routing-guide.md` [[context-routing-guide]] — the situational reading-order table
  this system governs
- `shared/memory-map.md` [[memory-map]] — the canonical-memory index this system draws
  packets from
- `templates/CONTEXT_PACKET_TEMPLATE.md` [[CONTEXT_PACKET_TEMPLATE]] — the packet template
- `RESEARCH_SYSTEM.md` [[RESEARCH_SYSTEM]] — where verified facts a packet carries come from
- `SELF_REPAIR_SYSTEM.md` [[SELF_REPAIR_SYSTEM]] — where stale/conflicting context becomes a
  repair target
- `ARCHIVE_RETENTION_SYSTEM.md` [[ARCHIVE_RETENTION_SYSTEM]] — the archive statuses behind this
  system's forbidden/historical context rules
- `HUMAN_INTERFACE_SYSTEM.md` [[HUMAN_INTERFACE_SYSTEM]] — applies this system's forbidden-context
  rule to what the operator dashboard should not surface
- `PROJECT_BOOTSTRAPPING_SYSTEM.md` [[PROJECT_BOOTSTRAPPING_SYSTEM]] — where a new project's default
  context stack is set up once bootstrapped
- `emergence/README.md` [[emergence/README]] — where recurring context-routing gaps become
  insights
- `shared/hpom.md` [[hpom]] — the authority tiers governing who may summarize vs.
  decide
- `Guidelines/MAP_repo_systems_gap_review.md` — the gap review that
  identified this system as priority #3
