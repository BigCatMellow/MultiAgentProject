# E/I External Benchmark Report: MAP 2026-07-15

## Summary

MAP is, in 2026 terms, a **supervisor + durable-blackboard + swarm-handoff hybrid**. Its differentiator is durability: a file/SQLite blackboard (`tasks/`, `shared/`, `events.jsonl`, `map.db`) plus mechanical release/task gates, where most competitor frameworks keep coordination state in memory and bolt persistence on later. The strategic risk is inward-building: MAP keeps adding infrastructure without a working-backwards external customer workflow.

## Framework Landscape

| Framework | Core Topology | State Model | What MAP Can Learn |
|-----------|---------------|-------------|-------------------|
| LangGraph | Directed graph + conditional edges, checkpointing w/ time-travel | Durable checkpointer | MAP has a LangGraph runner (`graph/runner.py`) + `MapSqliteSaver`, but task flow is file/CLI-driven not graph-driven; graph topology could express waves/branches more explicitly. |
| CrewAI | Role-based crews (role/backstory/goal + tasks) | Mostly in-memory | MAP's role docs (architect, reviewer, helper) already do this durably. |
| AutoGen/AG2 | Conversational GroupChat, message-driven | In-memory + enterprise sandboxing/identity/policy | MAP's hcom is the message bus; AutoGen's sandbox/identity/policy controls echo MAP's permission-levels + gates. |
| OpenAI Agents SDK / Swarm | Supervisor handoffs | Lightweight | Validates MAP's orchestrator-handoff model. |

## Orchestration Patterns (The 2026 "5 That Work")

The five proven patterns are: **fan-out** (parallel scatter-gather), **pipeline** (sequential chain), **debate** (multi-perspective critique), **supervisor** (hierarchical delegation), and **swarm** (peer handoff + shared blackboard).

MAP uses several well:
- **Supervisor** via the orchestrator pattern
- **Pipeline** via cross-review lanes
- **Fan-out** via task waves
- **Swarm** via hcom handoffs

MAP **underuses debate**—even though `hcom run debate` already exists as infrastructure. See IDEA-0019 for a proposal to promote debate to a first-class review decision mode.

## Agent Observability & Evals (Industry State 2026)

The 2026 consensus on dominant failure modes centers on three categories, not model errors: **tool-call failures**, **context truncation**, and **runaway loops**.

The industry standard for eval discipline is three-layered:
- **Unit-evals** on discrete steps
- **LLM-as-judge regression suites**
- **Continuous production trace sampling**

OpenTelemetry GenAI semantic conventions maintain vendor-agnostic traces, and cost models are token-weighted per-user attribution.

For MAP: `events.jsonl` is trace-shaped but unsampled/unscored; gates + `map_metrics.py` + the MAP-runtime health card (TASK-182/203) form the substrate. See IDEA-0018 for a proposal to formalize the three-layer eval discipline.

## Innovator Business-Model Philosophy → MAP

Three principles apply here:

**Amazon Working Backwards**: Define end-customer experience first (via PR/FAQ), then work backwards. MAP's proving workflow is still unpicked; `shared/improvement-backlog.md` lists "Decide first real general MAP workflow target" as OPEN. See INS-0023.

**Two-Pizza Teams**: Small, autonomous teams measured by a well-defined metric set, owning ALL aspects of their area. The implication for MAP: per-agent ownership metrics. See IDEA-0020.

**Day 1 Culture**: Customer obsession, long-term value over short-term gains, many bold bets. For MAP: avoid "Day 2" inward drift that adds infrastructure without external workflow validation.

## Recommendations (Ranked)

1. **Run a working-backwards PR/FAQ** to pick MAP's first real proving workflow (addresses the standing OPEN backlog item). [highest leverage]
2. **Formalize the three-layer eval discipline**, starting lightweight: the incident taxonomy (`notes/agent-incident-taxonomy.md`) + one LLM-as-judge review-quality check.
3. **Wire `hcom run debate`** into the conflict-freeze / decision-authority path as an optional pre-escalation step.
4. **Pilot per-agent two-pizza ownership metrics** in `map_metrics.py`.

## Sources

- https://www.digitalapplied.com/blog/multi-agent-orchestration-5-patterns-that-work
- https://gurusup.com/blog/agent-orchestration-patterns
- https://cordum.io/blog/ai-agent-frameworks-comparison
- https://openagents.org/blog/posts/2026-02-23-open-source-ai-agent-frameworks-compared
- https://www.digitalapplied.com/blog/agent-observability-2026-evals-traces-cost-guide
- https://andriifurmanets.com/blogs/ai-agents-2026-practical-architecture-tools-memory-evals-guardrails
- https://aws.amazon.com/executive-insights/content/amazon-two-pizza-team/
- https://www.fearlessculture.design/blog-posts/how-amazon-built-a-culture-of-innovation-by-working-backwards
