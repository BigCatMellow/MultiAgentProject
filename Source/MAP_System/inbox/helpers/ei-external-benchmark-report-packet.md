# Work Packet: E/I External Benchmark Report + Agent-Incident Taxonomy

- Owner (accountable): gune (orchestrator)
- Helper role: author two markdown files from the material below. Formatting +
  prose expansion only. Do NOT invent new claims, sources, or recommendations
  beyond what is given here. If something is unclear, leave a `TODO(gune):` note
  rather than guessing.
- Source of record: gune's E/I research wave (2026-07-15). Emergence records
  already created: INS-0022, INS-0023, IDEA-0018, IDEA-0019, IDEA-0020.

## Output paths (create exactly these two files)

1. `MAP_System/artifacts/reports/ei-external-benchmark-2026-07-15.md`
2. `MAP_System/notes/agent-incident-taxonomy.md`

Register both in any task record if this gets promoted; for now they are
E/I artifacts owned by gune.

---

## FILE 1 — ei-external-benchmark-2026-07-15.md

Purpose: durable record of how MAP compares to best-in-class 2026 multi-agent
systems and what innovator business-model philosophy implies for MAP. Audience:
core agents + operator. Keep it tight (~2 pages). Use these sections:

### Section: Summary (3–5 sentences)
MAP is, in 2026 terms, a **supervisor + durable-blackboard + swarm-handoff
hybrid**. Its differentiator is durability: a file/SQLite blackboard
(`tasks/`, `shared/`, `events.jsonl`, `map.db`) plus mechanical release/task
gates, where most competitor frameworks keep coordination state in memory and
bolt persistence on later. The strategic risk is inward-building: MAP keeps
adding infrastructure without a working-backwards external customer workflow.

### Section: Framework landscape (comparison table)
Build a markdown table with columns: Framework | Core topology | State model |
What MAP can learn. Rows and content:
- LangGraph — directed graph + conditional edges, checkpointing w/ time-travel |
  durable checkpointer | MAP HAS a LangGraph runner (`graph/runner.py`) +
  `MapSqliteSaver`, but task flow is file/CLI-driven not graph-driven; graph
  topology could express waves/branches more explicitly.
- CrewAI — role-based crews (role/backstory/goal + tasks) | mostly in-memory |
  MAP's role docs (architect, reviewer, helper) already do this durably.
- AutoGen/AG2 — conversational GroupChat, message-driven | in-memory + enterprise
  sandboxing/identity/policy | MAP's hcom is the message bus; AutoGen's
  sandbox/identity/policy controls echo MAP's permission-levels + gates.
- OpenAI Agents SDK / Swarm — supervisor handoffs | lightweight | validates
  MAP's orchestrator-handoff model.

### Section: Orchestration patterns (the 2026 "5 that work")
List: fan-out (parallel scatter-gather), pipeline (sequential chain), debate
(multi-perspective critique), supervisor (hierarchical delegation), swarm
(peer handoff + shared blackboard). State which MAP already uses well
(supervisor via orchestrator; cross-review **pipeline**; fan-out via task
waves; swarm via hcom handoffs) and which it **underuses: debate** — even
though `hcom run debate` already exists. Cross-ref IDEA-0019.

### Section: Agent observability & evals (industry state)
Report the 2026 consensus, attributed to the research:
- Dominant failure modes: tool-call failures, context truncation, runaway loops
  (NOT model errors).
- Three-layer eval framework: unit-evals on discrete steps; LLM-as-judge
  regression suites; continuous production trace sampling.
- OpenTelemetry GenAI semantic conventions keep traces vendor-agnostic.
- Cost model = token-weighted per-user attribution.
Map to MAP: `events.jsonl` is trace-shaped but unsampled/unscored; gates +
`map_metrics.py` + the MAP-runtime health card (TASK-182/203) are the substrate.
Cross-ref IDEA-0018.

### Section: Innovator business-model philosophy → MAP
- Amazon **working backwards**: define end-customer experience first (PR/FAQ),
  work backwards. MAP's proving workflow is still unpicked
  (`shared/improvement-backlog.md` "Decide first real general MAP workflow
  target" = OPEN). Cross-ref INS-0023.
- **Two-pizza teams**: small, autonomous, measured by a well-defined metric set,
  owning ALL aspects of their area. Implication: per-agent ownership metrics.
  Cross-ref IDEA-0020.
- **Day 1 culture**: customer obsession, long-term value over short-term,
  many bold bets. Framing: MAP should avoid "Day 2" inward drift.

### Section: Recommendations (ranked, as recommendations not decisions)
1. Run a working-backwards PR/FAQ to pick MAP's first real proving workflow
   (addresses the standing OPEN backlog item). [highest leverage]
2. Formalize the three-layer eval discipline, starting lightweight: the
   incident taxonomy (FILE 2) + one LLM-as-judge review-quality check.
3. Wire `hcom run debate` into the conflict-freeze / decision-authority path as
   an optional pre-escalation step.
4. Pilot per-agent two-pizza ownership metrics in `map_metrics.py`.

### Section: Sources
Reproduce this list verbatim as markdown links:
- https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work
- https://gurusup.com/blog/agent-orchestration-patterns
- https://cordum.io/blog/ai-agent-frameworks-comparison
- https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared
- https://www.digitalapplied.com/blog/agent-observability-2026-evals-traces-cost-guide
- https://andriifurmanets.com/blogs/ai-agents-2026-practical-architecture-tools-memory-evals-guardrails
- https://aws.amazon.com/executive-insights/content/amazon-two-pizza-team/
- https://www.fearlessculture.design/blog-posts/how-amazon-built-a-culture-of-innovation-by-working-backwards

---

## FILE 2 — notes/agent-incident-taxonomy.md

Purpose: a small, standing reference that names the failure modes MAP should
watch for in `events.jsonl` / RnS, so future eval + observability work has a
shared vocabulary. Keep it to one page. Include the HPOM metadata header block
copied in the SAME shape as the top of `MAP_System/notes/orchestration-notes.md`
(the `<!-- hpom: ... -->` lines) but with:
- file: notes/agent-incident-taxonomy.md
- project: MAP
- state_owner: command-center
- status: CURRENT
- last_verified: 2026-07-15
- verified_against: gune E/I research wave 2026-07-15
- confidence: MEDIUM
- supersedes: NONE
- superseded_by: NONE

Body: a table `Incident class | What it looks like in MAP | Existing coverage |
Gap`. Rows:
- tool-call failure — a script/gate/CLI call errors or returns wrong exit code |
  partly caught by `run_tests.sh`, gate exit checks | no structured incident tag
  in events.jsonl.
- context truncation — agent loses earlier task/claim state, re-derives wrong |
  brain-compaction + SYN-0001 (one-state-two-readers) mitigate | no detector.
- runaway loop — agent retries/repeats without progress (e.g. re-review dupes) |
  RnS + limit-watcher + announce-before-claim | no loop counter.
- silent stop / idle — session stops without handoff | limit-watcher reports,
  declared-idle (TASK-084) | covered, keep.
Close with a one-line pointer: this taxonomy seeds IDEA-0018's eval discipline.

---

## Must-not
- Do not edit `emergence/INDEX.md` (already rebuilt) or any `tasks/*.json`.
- Do not add sources/claims not listed above.
- Do not push or commit.

## Verify before reporting done
- Both files exist at the exact paths.
- `python3 MAP_System/scripts/validate_shared_state.py` is NOT required (these
  aren't shared/ files), but run
  `python3 MAP_System/scripts/map_emergence.py validate` to confirm nothing
  broke, and report the last line.
- Reply in hcom to @gune with: files written + the validate result line.
