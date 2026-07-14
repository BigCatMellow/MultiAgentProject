# MAP Repo Review List

Every repo surfaced while researching MAP. Organized by what problem it touches. Star counts and descriptions are from GitHub search results in July 2026 — verify current state before relying on any claim, especially token-savings percentages, which are self-reported.

Companion to: System-Requirements-Outline, Philosophical-Foundations, Thesis, Cross-Domain-Research (I, II, III), Lessons-Learned.

---

## Token Compression / Output Waste

- **headroomlabs-ai/headroom** — compress tool outputs/logs/files/RAG chunks before LLM. Library + proxy + MCP server. `headroom wrap claude|codex`. Own compression model (`kompress-v2-base`) on HF. Also has `headroom learn` (mines failed sessions → writes corrections to CLAUDE.md/AGENTS.md).
- **JuliusBrussee/caveman** — Claude Code skill, telegraphic output style, claims 65% token cut on output.
  - **JuliusBrussee/caveman-code**, **amanattar/caveman-claude-skill** — forks/variants
  - **JuliusBrussee/cavemem** — cross-agent persistent memory, compressed, local-first (companion to caveman)
  - **wilpel/caveman-compression** — more formal semantic compression (strip predictable grammar, keep facts)
  - **kuba-guzik/caveman-micro** — 6-line/85-token version, claims it outperforms the original
  - **InterfaceX-co-jp/genshijin** — Japanese-language adaptation
- **getagentseal/codeburn** (`npx codeburn`) — local token usage/cost tracker across 31 agent tools, by model/project/task. Diagnostic, not compression.
  - **rossnoah/codeburn-rs** — Rust rewrite, "600x faster"

## Knowledge Graphs / Codebase Ingestion

- **Graphify-Labs/graphify** — turns a folder (code, SQL, docs, images, video) into a queryable knowledge graph. Works with Claude Code, Codex, OpenCode, Cursor, Gemini CLI.
  - **lucasrosati/claude-code-memory-setup** — Obsidian + Graphify combo, claims 71.5x token reduction per session, persistent memory + chat import pipeline
  - **elbruno/graphify-dotnet** — .NET port
  - **TtTRz/graphify-rs** — Rust rewrite
  - **HKUST-KnowComp/DeepRefine-Skill** — academic, test-time graph refinement ("LLM-Wiki/Graphify")

## Wikilinks / Obsidian-as-Memory (direct relevance to librarian bot)

- **iurykrieger/claude-bedrock** — Claude Code plugin, Obsidian vault → entity-typed Zettelkasten graph (actors/people/teams/topics), bidirectional wikilinks, ingests Confluence/Google Docs/GitHub/docling files. Local markdown only, opt-out error reporting, never transmits vault content. **Closest existing match to the librarian bot design.**
- **ccf/agentcairn** — long-term cross-project agent memory, Obsidian vault as source of truth, daemonless, no opaque DB, local-first/user-owned.
- **BetaBots-LLC/callimachus** — one local searchable index of agent history across Claude Code/Codex/Cursor/Gemini. Keyword + semantic search, MCP server, CLI, VS Code extension.

## Agent Memory Layers (general)

- **mem0ai/mem0** — the de facto standard, "universal memory layer for AI agents." Read for extract/retrieve architecture even if not adopted.
- **EverMind-AI/EverOS** — local-first, **Markdown-native**, user-owned, self-evolving memory across apps/tools/workflows. Closest match to your Wikilinks/Markdown plan outside the Obsidian-specific tools.
- **MemTensor/MemOS** — "self-evolving memory OS," hybrid retrieval, cross-task skill reuse, claims 35.24% token savings (verify methodology).
- **MemoriLabs/Memori** — agent-native memory infra, turns execution/conversation into structured persistent state.
- **MemPalace/mempalace** — claims "best-benchmarked open-source AI memory system," free.
- **memvid/memvid** — serverless single-file memory layer, alternative to full RAG pipelines.
- **alash3al/stash** — Postgres-backed episodes/facts/working-context memory, MCP server, self-hosted single binary.
- **grapeot/context-infrastructure** — persistent memory + personal rules + skills + scheduled observations for coding agents.
- **Eshaan-Nair/ArcRift** — syncs context/decisions from browser chats (Claude, ChatGPT, DeepSeek) into local IDE agents via local SQLite knowledge graph.
- **sdwolf4103/opencode-working-memory** — persistent workspace memory + hot session context + compaction-based extraction, zero extra API calls.
- **Siddhant-K-code/distill** — context intelligence: write-time dedup, sensitivity tagging, conflict detection, hierarchical decay, ~12ms, no LLM calls, MIT.
- **uudam42/agent-memory-engine** — local-first MCP server, builds project knowledge base automatically, retrieves relevant architecture/constraints/incidents pre-task, retains verified lessons post-task.
- **Roshan02-CIT/Knowledge-graph-driver-rag-for-agentic-coding-tools** — 0★ but important **design pattern**: builds RKAG from ASTs/call-graphs/docstrings via tree-sitter, hybrid KAG+PPR retrieval, **dynamic token-budget agent capped at ≤3 hops**. Steal the hop-limit + budget-cap idea regardless of repo maturity.

## Multi-Agent Orchestration (general/commodity)

- **omnigent-ai/omnigent** — meta-harness orchestrating Claude Code/Codex/Cursor/Pi/custom agents, swappable without rewriting, policy/sandboxing enforcement. Closest architectural cousin to MAP's harness-agnostic goals.
- **open-multi-agent/open-multi-agent** — TypeScript, coordinator decomposes goal into task DAG across Claude/GPT/Gemini/local models.
- **Yeachan-Heo/oh-my-claudecode** — teams-first multi-agent orchestration for Claude Code.
- **builderz-labs/mission-control** — self-hosted dispatch/monitoring dashboard, spend tracking, multi-agent workflows.
- **wshobson/agents** — multi-harness plugin marketplace (Claude Code, Codex, Cursor, OpenCode, Copilot, Gemini).
- **golutra/golutra** — unifies Codex/Claude Code/OpenClaw, parallel execution, long-running workflows.
- **jnMetaCode/agency-agents-zh** + **jnMetaCode/agency-orchestrator** — 266 plug-and-play expert personas (Chinese market focus), DAG orchestration from one sentence.
- **cft0808/edict** — 9 specialized agents, real-time dashboard, audit trails.

## "AI Software Company" / Business-Role Frameworks (closest to MAP's org metaphor — but different layer)

- **FoundationAgents/MetaGPT** — `Code = SOP(Team)`. One-line requirement → PM/architect/PjM/engineer pipeline → repo. Linear fixed pipeline, one-shot generator, no persistent shared-state coordination, no MATOCP equivalent. Try the HuggingFace demo before adopting or dismissing.
- **ChatDev** (see also `zGeneral/chatdev-harness` — reimplemented as Claude Code subagent harness: spec→build(TDD)→review→test) — virtual software company, role-agents write real files.
- **HDAnzz/ClawDev** — ChatDev + openclaw hybrid, custom workflow/character design.
- CrewAI — mentioned in comparison lists, not yet pulled directly; reputed to be closer to persistent role-teams than MetaGPT's one-shot factory. **Worth fetching README next.**

## Multi-Agent Collaboration Mechanics (shared memory, gating — closest to MAP's actual coordination layer)

- **WenyuChiou/agent-collab-skills** — task splitter, output reconciler, adversarial debate, shared memory, **acceptance gate**. Composes with codex-delegate/gemini-delegate. Check whether their acceptance-gate already implements your threshold-safeguard idea.

## Ollama / Local-Model Integration

- **swarmclawai/swarmclaw** — self-hosted agent runtime, memory, MCP tools, schedules, delegation, 23+ providers incl. Ollama. "Practical Claude Code/LangChain alternative."
- **milisp/codexia** — lightweight workstation for Codex CLI + Claude Code, task scheduler, **git worktree management**, remote control, skills management. Closest existing tool to your git-locking/worktree problem, though only as scheduling convenience, not a full fix.
- **stacklok/codegate** — security, workspaces, multiplexing for agentic frameworks.
- **prajwalshettydev/UnrealGenAISupport** — UE5 plugin, many providers incl. Ollama, NPC AI/agentic — not directly relevant unless MAP ever touches game dev tooling.
- **macOS26/Agent** — Mac agentic harness, 18+ providers, computer use/automation.

## Design Language (for UI-facing MAP components / Onyx / Mellow work)

- **pbakaus/impeccable** — design language that makes agent-generated UI look intentional, not generic. Companion: **pbakaus/impeccable-talks** (conference talks). Applied example: **peterhadorn/webdesign-agency-skills**.

## Usage / Cost Monitoring & Observability (measure whether MATOCP/laziness-ladder are working)

- **simple10/agents-observe** — real-time dashboard plugin, full session-lifecycle hooks, subagent hierarchy, session replay, per-model token stats, local SQLite.
- **mishanefedov/agentwatch** — simpler local-only "one timeline across agents."
- **hoangsonww/Claude-Code-Agent-Monitor** — self-hosted dashboard via native hooks, live sessions/subagent trees.
- **Ventuss-OvO/cc-costline** — statusline showing 7d/30d spend.

## Retrieval Framework (for pipeline architecture reference)

- **deepset-ai/haystack** — production modular retrieval pipelines (ingest→chunk→retrieve→rerank as swappable stages). Read for structure, not necessarily to adopt.

## Curated "Awesome" Lists (compiled by others — mine periodically, they update)

- **hesreallyhim/awesome-claude-code** — hand-picked, quality-filtered (not just star count). Has direct sections: Providers/Runtime/Integration Infra, Documentation/Knowledge/Learning, Multi-Agent Orchestration, Skills, Memory & Context Persistence, Usage & Cost Monitoring, Observability, Security, Infrastructure & DevOps. Also keeps `README_ALTERNATIVES/` for maintained "legacy" tools worth checking.
- **e2b-dev/awesome-ai-agents** — broad agent landscape, open-source vs. closed-source split.
- **e2b-dev/awesome-sdks-for-ai-agents** — companion list, frameworks/SDKs specifically (more relevant to MAP than the agents list itself).
- **vivy-yi/awesome-agent-orchestration** — curated comparison: AutoGen, CrewAI, MetaGPT, LangGraph, Swarms.
- **Vincentwei1021/awesome-ai-agent-frameworks** — Chinese-language guide with a framework selection decision tree.

## Design Systems / Business Vocabulary (obscure, low-confidence, worth a skim only)

- **imdeepthakkar/deeps-agentic-os** — "Deep's Agentic OS," Obsidian Graphify brain + "SEED & PAUL builders framework." 1★, single-person project, but PAUL's actual mechanics never confirmed — worth a quick look if the framework concept resurfaces.

---

## Priority Read Order (if time is short)

1. **iurykrieger/claude-bedrock** and **ccf/agentcairn** — direct blueprints for the librarian bot.
2. **Roshan02-CIT/Knowledge-graph-driver-rag-for-agentic-coding-tools** — steal the hop-limit/token-budget pattern regardless of stars.
3. **WenyuChiou/agent-collab-skills** — check their acceptance-gate against your threshold-safeguard design.
4. **milisp/codexia** — closest existing tool to the git-worktree/locking problem.
5. **FoundationAgents/MetaGPT** (HuggingFace demo) — fastest way to confirm MAP is solving a different layer than the "AI company" frameworks.
6. **omnigent-ai/omnigent** — if you ever want to stop building your own harness-routing layer.
