# MAP Tool-Evaluation Appendix
### Candidate Libraries and Repos — With a Verdict on Each

This appendix evaluates the external tools and repositories surfaced in the repo-survey session, against the components of the synthesized MAP system. It complements the existing `MAP-Repo-Review-List.md` (which lists everything with read-order); this document takes a position on **whether each one should be adopted, studied, or skipped**, and where it fits.

The governing discipline is the one the simulation kept proving: **every external tool is a new dependency and a new mechanism. It must earn its place by measurement, not adoption by default (Braess).** Two recurring cautions apply to nearly everything below:
- **"Fewer tokens / same answer" is a vendor claim — verify what it silently drops on your traffic** (the lossy-summary and convergence≠correctness lessons).
- **Anything that sits between your agents and the model reads everything** — check maintenance health and what it logs before routing traffic through it.

---

## Cluster 1 — Token Compression / Context Economy
*Fits: component 9 (Knowledge layer) and MATOCP. These attack "fewer tokens, same answer" at different points in the pipeline.*

| Tool | What it does | Verdict | Fit |
|---|---|---|---|
| **LLMLingua** (Microsoft Research) | Prompt compression before submission; research-backed with published papers | **Study first / strongest candidate.** The most rigorously validated option here — real prior art for MATOCP. | Pre-submission compression; the reference model for MATOCP's token-optimization goal |
| **headroom** (headroomlabs-ai) | Compresses tool outputs, logs, files, RAG chunks in transit; library/proxy/MCP | **Evaluate as the transient-payload compressor**, in *library* mode (avoid routing all traffic through the proxy). Measure what it drops. | Complements the Library agent: it compresses ephemeral payloads, the Library agent compresses durable docs |
| **caveman** (+ variants), **codeburn** | Token-compression tools in the same family | **Skip unless headroom/LLMLingua disappoint.** Redundant with the two above; no reason to evaluate three compressors at once (Braess). | Same slot as headroom |
| **leanctx, clipforge-PAKT, harness-evolver** | Prompt pre-processing / pre-submission optimization | **Park.** Study only if LLMLingua proves insufficient. | Pre-submission layer |

**Bottom line:** adopt *one* transient-payload compressor (headroom, library mode) and study LLMLingua as the model for MATOCP. Do not stack multiple compressors — each adds a dependency and a place for silent data loss.

---

## Cluster 2 — Memory / Knowledge-Graph Systems
*Fits: component 9 (where the corpus lives) and component 5 (where emergence's learned heuristics persist). This is a real gap the synthesized system otherwise hand-waves as "memory."*

| Tool | What it does | Verdict | Fit |
|---|---|---|---|
| **mem0** | Persistent agent-memory layer; the most established option | **Evaluate as the memory backend.** Most mature; directly addresses "where do learned heuristics live across restarts." | Emergence heuristic persistence + Library corpus store |
| **MemOS** | Memory-operating-system for agents | **Study alongside mem0.** Newer, more ambitious; compare against mem0's maturity. | Same slot |
| **Graphify** | Knowledge-graph construction | **Study for the wikilink-graph mechanics** specifically — how it builds and queries a linked graph. | Library agent's graph layer |
| **EverOS, iurykrieger/claude-bedrock, ccf/agentcairn** | Memory/agent-infra variants | **Skim, low priority.** Note for completeness; evaluate only if mem0/MemOS don't fit. | Memory layer alternatives |

**Bottom line:** the memory-persistence gap is real and worth closing deliberately. Evaluate mem0 first (maturity), MemOS second (ambition), Graphify for graph mechanics. But weigh against the simpler default already in the synthesized doc — **WAL-mode SQLite with the event/causal/snapshot schema** — which may be sufficient and dependency-free. Adopt a memory system only if it beats plain SQLite for your actual needs.

---

## Cluster 3 — Orchestration Frameworks
*Fits: nothing new — this is the commodity layer MAP already has. Included because the survey's conclusion is worth preserving.*

| Tool | Verdict | Why |
|---|---|---|
| **MetaGPT** | **Study, don't adopt.** | Uses a **fixed linear pipeline**, not MAP's coordinate-through-shared-state model — which is precisely why it doesn't address correctness-under-concurrency. Reading it confirms MAP's differentiation. |
| **CrewAI** | **Reference only.** | Good local-model support and role modeling; but orchestration routing is now commodity and CrewAI doesn't solve MAP's plumbing gap. |
| **omnigent, open-multi-agent** | **Skim.** | Same category; no unique contribution to MAP's actual hard problems. |

**Bottom line — the key survey finding:** orchestration routing is commodity; MAP's genuine, unaddressed gap is **correctness-under-concurrency** (atomic task IDs, cross-process locking, drift resolution, the standardized protocol). None of these frameworks solve that. This is the strongest confirmation that MAP's value is its plumbing, not its routing — and a reason *not* to adopt a framework that would replace the routing while leaving the plumbing gap open.

---

## Cluster 4 — Integration Libraries (integrate into MAP, don't replace it)
*Fits: various components. These are libraries you'd call, not frameworks you'd hand control to.*

| Tool | What it does | Verdict | Fit |
|---|---|---|---|
| **LangFuse** | Observability / tracing for LLM apps | **Evaluate against the SQLite-event-schema approach for component 8.** A real alternative to hand-rolling the trace layer — but adds a dependency; compare honestly. | Observability (component 8) |
| **DSPy** | Systematic prompt optimization / compilation | **Study for emergence and the validator.** Could sharpen the gap-inference prompts and the validator's accuracy (the ~1% false-positive target). | Emergence (5), Validator (4) |
| **LangGraph** | State-graph orchestration | **Reference for checkpointing patterns only.** Already studied; its state/checkpoint model informed the canonical-state design. Don't adopt wholesale. | Canonical state (2) — pattern reference |
| **LangChain** | General LLM toolkit | **Skip as a framework; cherry-pick utilities if ever needed.** Broad and heavy; nothing MAP specifically needs. | — |

**Bottom line:** two worth real evaluation — **LangFuse** (does it beat SQLite for observability?) and **DSPy** (can it drive the validator's false-positive rate down and sharpen emergence?). The rest are pattern references, already absorbed.

---

## Consolidated Recommendation

If acting on this appendix, evaluate in this order (highest leverage first), and adopt only what beats the dependency-free default on measurement:

1. **LLMLingua** — study as the model for MATOCP token optimization (research-backed).
2. **mem0 vs. plain WAL-SQLite** — settle where memory/heuristics live; adopt mem0 only if it beats SQLite for your needs.
3. **LangFuse vs. SQLite-event-schema** — settle the observability layer the same way.
4. **DSPy** — evaluate for driving validator accuracy to the ~1% false-positive target.
5. **headroom** (library mode) — adopt as the transient-payload compressor if it measurably helps without dropping needed detail.
6. Everything else — skim, keep on the list, evaluate only if a primary choice disappoints.

**The meta-point:** the synthesized system is deliberately buildable with near-zero dependencies (Python stdlib + `filelock` + SQLite). Every tool above is an *optional upgrade* to a specific component, to be adopted only when measurement shows it beats the simple default — never adopted as a bundle. That discipline is what keeps MAP from re-accumulating the complexity the simulation spent seven rounds stripping out.

---

*Companion to MAP-The-Synthesized-System.md and the existing MAP-Repo-Review-List.md. Architecture-level ideas from the repo-survey session (transit/infrastructure cross-domain models, the memory-persistence gap) are folded into the synthesized system doc itself; this appendix holds the tool/repo shopping, which will change over time.*
