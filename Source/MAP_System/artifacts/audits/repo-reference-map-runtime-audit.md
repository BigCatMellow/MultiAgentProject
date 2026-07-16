# Repo Reference Runtime Audit

Task: TASK-171
Owner: codex-lab-mozu
Date: 2026-07-14
Status: draft for review
Scope: `/home/home/Projects/MultiAgentProject/repo`

## Purpose

Survey the newly added `repo/` reference folder for patterns that can help MAP.
This audit focuses on MAP runtime concerns: orchestration, memory, context
compression, observability, cost/yield tracking, and agent-instruction
packaging.

This is a reference audit only. No external code is copied into MAP, and no
dependency adoption is recommended without a follow-on task, local measurement,
and review.

## Coordination

`claude-lab-zera` took the wikilink / knowledge-graph cluster and recorded
findings in:

- `MAP_System/artifacts/research/NOTE-0003-local-repo-drop-survey.md`

This audit avoids duplicating that lane and covers the runtime-oriented cluster:

- `headroom-main`
- `caveman-main`
- `EverOS-main`
- `MemOS-main`
- `Memori-main`
- `mem0-main`
- `MetaGPT-main`
- `haystack-main`
- `agents-observe-main`
- `codeburn-main`
- `impeccable-main` / `universal`
- `awesome-claude-code-main`

## Inventory Notes

The folder contains both extracted directories and archives. Many projects have
versioned and `main` copies; this audit used the `*-main` trees where present,
and versioned trees only as confirmation.

Important noise / duplicate categories:

- UI libraries named `headroom.js`, `react-headroom`, and
  `svelte-headroom` are unrelated to Headroom AI context compression.
- Archives such as `*.zip`, `*.tar.gz`, `*.whl`, and `*.deb` are retained as
  reference packages, but this audit read extracted source trees.
- Some projects require network services, API keys, Docker, native binaries, or
  hosted platforms. Treat those as architectural references, not install
  candidates.

## Findings

### 1. Best Immediate MAP Pattern: Event/Session Observability

Reference:

- `repo/agents-observe-main/README.md`
- `repo/agents-observe-main/hooks/scripts/observe_cli.mjs`
- `repo/agents-observe-main/app/server/src/storage/sqlite-adapter.ts`
- `repo/agents-observe-main/app/server/src/routes/events.ts`
- `repo/agents-observe-main/app/server/src/transcript-parser/agents/codex.ts`

Useful idea:

Agents Observe treats hook events and transcripts as the ground truth, stores
them in local SQLite, and exposes live replay/search/filter views. MAP already
has `events/events.jsonl`, hcom events, task state, and mission-control TUI
panels, but lacks a first-class session replay model.

MAP fit:

- Strong fit for mission-control next phase.
- Use the architecture pattern, not the Node/Docker implementation.
- Translate the idea into a MAP-native event replay index:
  `events.jsonl` + hcom event IDs + task `trace_id` + local SQLite/materialized
  read model.

Recommended follow-up:

- Create a design task for `MAP session replay/read model`.
- Acceptance should require: no new write authority, local-only storage,
  trace/task/agent filters, and drift checks against canonical event/task
  sources.

### 2. Best Immediate MAP Pattern: Cost/Yield Accounting

Reference:

- `repo/codeburn-main/README.md`
- `repo/codeburn-main/src/providers/codex.ts`
- `repo/codeburn-main/src/context-tree.ts`
- `repo/codeburn-main/src/guard/`
- `repo/codeburn-main/src/yield.ts`
- `repo/codeburn-main/src/optimize.ts`

Useful idea:

CodeBurn reads existing local session files and converts them into cost, model,
tool, project, context-tree, and yield views. The key pattern is not cost
pricing itself; it is the local-first rollup from existing session artifacts,
with explicit categories such as tool-result tokens, assistant reasoning, model
cost, productive/reverted/abandoned spend, and guardrails.

MAP fit:

- Strong fit for MAP cost governance and mission-control vitals.
- MAP already has a cost-governance subsystem, but it is event-level and
  dispatch-focused. It does not yet answer "what did this work cost and what
  actually shipped?"

Recommended follow-up:

- Add a MAP cost/yield audit task that derives:
  - cost by task;
  - cost by agent/model lane;
  - cost by output path or released task;
  - cost lost to abandoned or reworked tasks;
  - estimated tool-output/context pressure from hcom/Codex transcripts where
    available.

Do not install CodeBurn into MAP as a dependency. Use it as a source of
categories and local-file parsing ideas.

### 3. Best Immediate MAP Pattern: Content-Aware Compression Policy

Reference:

- `repo/headroom-main/README.md`
- `repo/headroom-main/headroom/transforms/content_router.py`
- `repo/headroom-main/headroom/transforms/content_detector.py`
- `repo/headroom-main/headroom/transforms/search_compressor.py`
- `repo/headroom-main/headroom/transforms/log_compressor.py`
- `repo/headroom-main/headroom/proxy/output_shaper.py`
- `repo/headroom-main/headroom/proxy/savings_tracker.py`
- `repo/caveman-main/README.md`

Useful idea:

Headroom has a content-router model: detect content type, protect exact file
reads, compress search/log/JSON output differently, and keep retrieval markers
for originals. Caveman shows a narrower output-style compression pattern and
honestly documents that output brevity can be net-negative if the skill adds too
much input overhead.

MAP fit:

- Strong fit for future MAP "Library layer" and hcom transcript compaction.
- Poor fit as a direct proxy/wrapper inside this lab until measured. Proxying
agent traffic changes trust and debugging boundaries.

Recommended follow-up:

- Run a measurement-only task on real MAP artifacts:
  - event logs;
  - run output;
  - task JSON;
  - handoffs;
  - reviews;
  - command transcripts.
- Measure compression ratio, detail-needed/re-read rate, validator pass rate,
  and whether exact-file-read protection is needed.

Recommended MAP design borrowing:

- Type-specific compaction policies.
- "Do not lossy-compress file content used for patches."
- Reversible summaries with local retrieval pointers.
- Output-shaping policy as a preference, not a default.

### 4. Best Memory Pattern For MAP: File-Backed Memory Plus Derived Index

References:

- `repo/EverOS-main/README.md`
- `repo/EverOS-main/src/everos/memory/cascade/`
- `repo/EverOS-main/src/everos/memory/strategies/`
- `repo/EverOS-main/src/everos/memory/search/`
- `repo/MemOS-main/README.md`
- `repo/MemOS-main/src/memos/multi_mem_cube/`
- `repo/MemOS-main/src/memos/mem_scheduler/`
- `repo/Memori-main/README.md`
- `repo/Memori-main/memori/memory/`
- `repo/Memori-main/core/docs/architecture.md`
- `repo/mem0-main/README.md`
- `repo/mem0-main/mem0/memory/`

Useful idea:

EverOS is closest to MAP's durable-file values: Markdown as source of truth,
SQLite/LanceDB as derived indexes, explicit user/agent tracks, and background
reflection/consolidation. MemOS, Memori, and mem0 add useful vocabulary:
multi-cube isolation, attribution, background ingestion, feedback/correction,
entity linking, hybrid retrieval, and temporal ranking.

MAP fit:

- EverOS architectural pattern is high fit.
- MemOS/Memori/mem0 are conceptually useful but too broad/heavy to adopt as
  dependencies. They lean toward product memory platforms; MAP needs local
  project memory with strict provenance and review gates.

Recommended follow-up:

- Design a MAP memory index that keeps Markdown/JSON as source of truth and
  builds disposable search indexes from:
  - decisions;
  - reviews;
  - task records;
  - handoffs;
  - emergence;
  - hcom summaries.
- Include source-path provenance, confidence, supersession, and "last verified"
  metadata. Do not store untraceable extracted facts.

### 5. Useful Orchestration Pattern: Components, Snapshots, Breakpoints

References:

- `repo/haystack-main/README.md`
- `repo/haystack-main/haystack/core/pipeline/pipeline.py`
- `repo/haystack-main/haystack/core/pipeline/base.py`
- `repo/haystack-main/haystack/core/pipeline/breakpoint.py`
- `repo/haystack-main/haystack/tracing/`
- `repo/MetaGPT-main/README.md`
- `repo/MetaGPT-main/metagpt/roles/`
- `repo/MetaGPT-main/metagpt/actions/`
- `repo/MetaGPT-main/metagpt/memory/`

Useful idea:

Haystack's pipeline model has explicit components, typed inputs/outputs,
tracing spans, snapshots, breakpoints, and runtime validation. MetaGPT's role
and SOP model is less directly useful because MAP already has its own task
system, but its role/action separation confirms MAP's direction: keep roles,
actions, and durable artifacts distinct.

MAP fit:

- Haystack pattern is useful for future runner refactors.
- MetaGPT is a "do not adopt" dependency; it is a different product layer.

Recommended follow-up:

- Add a design task for "runner component contracts" only if current runner
  complexity grows. Keep the present LangGraph runner until there is a concrete
  maintenance pain.
- Borrow:
  - component input/output validation;
  - snapshot/breakpoint vocabulary for restartable routes;
  - tracing spans mapped to MAP `trace_id`.

### 6. Agent-Instruction Packaging: Useful For Distribution, Not Runtime

References:

- `repo/impeccable-main/README.md`
- `repo/universal/README.txt`
- `repo/universal/.codex/hooks.json`
- `repo/universal/.agents/`
- `repo/awesome-claude-code-main/config.yaml`

Useful idea:

Impeccable and `universal/` show how one skill can be packaged across Codex,
Claude, Cursor, Gemini, OpenCode, GitHub Copilot, and others. Awesome Claude
Code shows a curated catalog model driven by structured config and generated
README/categories.

MAP fit:

- Useful if MAP becomes a reusable package or plugin.
- Not useful for current MAP runtime hardening.

Recommended follow-up:

- Defer. When MAP has a stable "installable collaboration system," create a
  packaging task that studies `universal/` and Impeccable's provider-specific
  hook/skill distribution.

## Not Recommended For Adoption Now

| Candidate | Reason |
|---|---|
| Direct Headroom proxy/wrap | Trust/debug boundary is too large; measure MAP-specific compaction first. |
| Caveman-style global terseness skill | MAP already has communication rules; output compression can hide needed review evidence if applied globally. |
| MetaGPT framework | Different product layer; MAP already has task ownership, review, runner, and hcom coordination. |
| MemOS/Memori/mem0 as dependency | Too broad/heavy; needs API keys, external services, vector/graph backends, or hosted platforms for core paths. Borrow concepts only. |
| Agents Observe as deployed service | Requires Docker/Node hooks; MAP should first build a read-only local replay index from its existing event sources. |
| CodeBurn as deployed cost system | Node tool aimed at many agent products; MAP should implement task-specific rollups using its existing cost governance and event/task data. |
| Impeccable design skill | Excellent frontend-specific package, but not relevant to MAP runtime except for future packaging/distribution patterns. |

## Recommended MAP Follow-Up Queue

Priority 1 — session replay / event read model:

- Design a MAP-native session replay index that joins `events.jsonl`, hcom
  events, task IDs, agent IDs, trace IDs, and review artifacts.
- Keep it read-only; mission-control can render it later.

Priority 2 — cost/yield rollup:

- Extend cost governance from "dispatch safe?" to "what did each task cost, and
  did it produce approved/released work?"
- Use local transcript/session parsing only when available, with privacy notes.

Priority 3 — library-layer measurement:

- Run compression/compaction measurements on real MAP files before designing
  any library layer.
- Include exact-read protection and re-read rate as acceptance criteria.

Priority 4 — MAP memory index design:

- Use file-backed source of truth with disposable derived index.
- Tag every memory item by source path, task/review/event, provenance, and
  confidence.

Deferred:

- Provider-agnostic skill/plugin packaging.
- External UI/CommandCenterUI integration.
- Direct adoption of any reference repo dependency.

## Bottom Line

There is useful material in `repo/`, but the value is mostly architectural.
The strongest MAP-relevant ideas are:

1. Agents Observe: replayable event/session observability.
2. CodeBurn: local cost/yield/accounting from existing session files.
3. Headroom: content-aware, reversible, measured compression policy.
4. EverOS: Markdown source of truth with disposable derived indexes.
5. Haystack: component contracts, snapshots, breakpoints, and tracing.

The safest next move is not installation. It is one or two focused MAP tasks
that adapt the patterns into MAP's existing durable-file, SQLite, hcom, review,
and mission-control architecture.

