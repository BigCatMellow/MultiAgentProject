# MAP System: A Comprehensive Requirements Outline
### Theoretical Foundations, Architectural Requirements, and Process Design for Multi-Agent Coordination Systems

---

## I. Preliminary Framing

### A. Problem Classification
MAP is not primarily an AI problem. It is a **distributed systems coordination problem** with an AI-driven execution layer. The correct study order is:
1. Distributed systems theory (governs correctness)
2. Organizational/process design (governs sustainability)
3. Multi-agent AI literature (governs the agent-specific failure surface)

Treating this as (3) alone — "how do I make my agents work together better" — is the most common mistake in this space and the likely source of several audit findings.

### B. Definitions Used Throughout
- **Agent**: an autonomous unit of execution (Claude Code, Codex, etc.) that can read state, act, and write state without a human in the loop for each step.
- **Orchestrator**: the component that decomposes tasks and dispatches them to agents (HPOM, in your system).
- **Coordination layer**: the channel through which agents report status and negotiate shared resources (hcom).
- **Canonical state**: the single, authoritative representation of "what is true right now" (the disputed repo).
- **Drift**: divergence between two copies of state that should be identical.
- **Race condition**: an outcome that depends on the non-deterministic timing of two or more concurrent operations.

---

## II. Distributed Systems Foundations (Required Reading)

### A. Concurrency Control
1. **Optimistic vs. pessimistic concurrency control**
   - Pessimistic = locks (your "git operation lock" fix)
   - Optimistic = version checks / compare-and-swap, retried on conflict
   - *Applies to*: task ID allocation, repo writes
2. **Compare-and-swap (CAS) and atomic operations**
   - Why "check then write" (two steps) is unsafe and "check-and-write" (one atomic step) is not
   - *Applies to*: atomic task ID allocator — this is the textbook CAS use case
3. **Idempotency**
   - An operation is idempotent if running it twice produces the same result as running it once
   - Idempotency keys: a unique token attached to an operation so retries are detected and ignored rather than reapplied
   - *Applies to*: agent action retries after timeout, hcom message delivery

### B. Consensus and Agreement (conceptual level only — full Paxos/Raft not required)
1. **Why "two writers, one truth" is a solved family of problems**
   - Leader election (one agent designated as write-authority at a time)
   - Quorum-based agreement (majority must agree before a write is accepted)
2. **CAP theorem (conceptual)**
   - Consistency, Availability, Partition tolerance — pick two
   - *Applies to*: deciding what hcom should do when agents can't reach the canonical repo — fail closed (consistency) or proceed with stale state (availability)?
3. **Byzantine fault tolerance (awareness level)**
   - Relevant only if you anticipate agents producing *actively contradictory* state, not just delayed state. Likely lower priority for MAP unless agent hallucination corrupts shared state.

### C. State Management
1. **Single source of truth pattern**
   - *Applies to*: canonical repo marker — this should be enforced structurally (one repo is physically the only writable one), not just documented
2. **Checkpointing and time-travel**
   - The ability to reconstruct system state at any prior point, not just the current point
   - Reference implementation to study: LangGraph's checkpointing model
3. **Event sourcing (alternative/complementary pattern)**
   - Store the sequence of events that produced the state, not just the state itself
   - Benefit: repo drift becomes detectable and often reversible, because you can replay events to find where two copies diverged
   - *Consider for*: emergence and hcom logs

---

## III. Architecture Patterns for Multi-Agent Systems

### A. Topology Selection
1. **Orchestrator-worker** (majority pattern in production systems)
   - Central orchestrator classifies, decomposes, dispatches, merges
   - Best fit when: task types are well-understood and hierarchy is acceptable
2. **Peer/blackboard**
   - No central control; agents read/write shared state and self-select work
   - Best fit when: task discovery itself is emergent (closer to what "emergence" seems to be doing)
3. **Federated**
   - Multiple canonical stores with explicit sync contracts between them
   - Best fit when: a single canonical repo becomes an availability or scaling bottleneck
   - *Recommended evaluation target for MAP's repo-drift problem*, as an alternative to enforcing one canonical repo

### B. Recommendation for MAP
Given known findings, MAP currently exhibits **orchestrator-worker execution (HPOM) with blackboard-style coordination (hcom) and no enforced single source of truth** — a hybrid that is not internally consistent. Priority: decide, explicitly, per subsystem, which topology it is, rather than allowing the ambiguity to persist.

---

## IV. Failure Taxonomy and Self-Diagnosis

### A. Reference Taxonomy
Cemri et al. (MAST-Data, 2025) — 1,600+ annotated execution traces across AutoGen, ChatDev, CrewAI — identifies 14 failure modes in three categories:
1. **System Design Issues**: improper task routing, inadequate error handling, resource contention
2. **Inter-Agent Misalignment**: communication breakdowns, conflicting objectives, coordination failures
3. **Task Verification Failures**: inadequate output validation, missing quality checks, error propagation

### B. Required Action
Score MAP against all 14 categories explicitly, not just the 9 findings already identified. The 9 findings may cluster in only 1–2 of the 3 categories, meaning entire failure classes (most likely Task Verification) may be currently unaudited.

### C. Continuous Self-Auditing (target end state)
Move from **manual, periodic audit** (current state) to **continuous, automated detection**:
- Event validator running at all times, not invoked on demand
- Agent availability reconcile script running on a schedule, not manually
- Structured trace output (see Section V) feeding automated anomaly detection, not just human review

---

## V. Observability Requirements

### A. Structured Logging
1. Every agent action should emit a structured record (not free-text logs): actor, action, target, timestamp, causal parent (what triggered this action)
2. Redaction/PII handling — likely low priority for personal-use MAP, but establish the pattern now while it's cheap

### B. Distributed Tracing
1. **Span model**: each unit of work (a task, a sub-task, a tool call) is a span; spans nest to form a trace
2. **Trace tree**: the full causal chain from task assignment to completion, viewable as one structure rather than scattered logs
3. Reference standard to study (concepts only, not necessarily adoption): OpenTelemetry span/trace model

### C. Metrics Separation
- Agent-local metrics (how one agent is performing) vs. system-wide metrics (how MAP as a whole is performing) should be tracked separately — conflating them hides which layer a problem originates in

---

## VI. Reliability Engineering Requirements

### A. Retry and Failure Handling
1. Idempotency keys on all write operations (ties to II.A.3)
2. Dead-letter queues: failed tasks go somewhere inspectable rather than silently dropping or infinitely retrying
3. Explicit replay policy: under what conditions is a failed task automatically retried vs. escalated to a human

### B. Error Containment
1. **Circuit breakers**: if an agent or subsystem fails repeatedly, stop routing work to it rather than continuing to feed a broken component
2. **Error boundaries**: one agent's failure should not corrupt shared state or cascade into other agents' decisions — this is distinct from the git lock fix, which prevents *concurrent* corruption; this prevents *cascading* corruption

### C. The Andon Principle (borrowed from Lean/Toyota Production System)
- Any component (agent, validator, human) should be able to halt the system the instant it detects a problem, rather than continuing and hoping downstream steps catch it
- *Directly applicable to*: the event validator — recommend it have unilateral authority to halt task dispatch, not just log/report

---

## VII. Governance and Human-in-the-Loop Design

### A. Pre-Dispatch Approval Gates
- High-risk actions (deletions, repo-structure changes, anything irreversible) should require a policy check *before* execution, not just be checked afterward by audit
- This upgrades the "operator intake checklist" from a manual document into an enforced gate the orchestrator itself runs

### B. Capability Whitelisting
- Explicit, enumerated list of what each agent is allowed to do (which tools, which repos, which operations)
- Absence of this is a common root cause in the "system design issues" category of the MAST taxonomy

### C. Escalation Paths
- Defined path for what happens when an agent is uncertain or two agents disagree — currently likely undefined in MAP; this is the AI-system analog of an org chart

---

## VII-bis. Compliance Enforcement (Ensuring the System Is Actually Followed)

### A. The Core Principle
Stop relying on agents *choosing* to comply. Make non-compliance either structurally impossible or automatically detected. A rule that lives only in a prompt or protocol document (e.g., MATOCP) is an instruction, not an enforcement mechanism — agents drift from it under context pressure.

### B. Structural Enforcement Over Instructional Enforcement
- Convert "should follow this format" into "cannot produce anything else"
- Schema validation that rejects malformed output *before* it is accepted, rather than trusting correct formatting
- This is the same principle as the atomic allocator/lock, applied to protocol shape rather than concurrency

### C. Separate Verification Layer (do not self-report)
- Do not ask an agent whether it followed protocol; check its output against protocol with a *different* component
- A lightweight validator (script or a dedicated compliance-checking agent) reviews hcom/emergence output against the MATOCP spec
- Real-life analogue: the **expediter** in a classical kitchen brigade — every plate passes one checkpoint before leaving the pass; stations are not trusted to self-report doneness
- *This is the single highest-leverage compliance fix — build it first*

### D. Compliance Telemetry
- Track *which* rules are violated and *how often*, not just pass/fail
- Frequently violated rule → probably badly specified or context-hostile (fix the protocol)
- Rarely violated rule → probably noise (fix nothing)

### E. Instruction Decay Over Long Sessions (likely root cause)
- Agents drift from a protocol as the context window fills — decay, not defiance
- Fix: periodic re-injection of core protocol rules at intervals or task boundaries, not just once at session start
- Related existing work: `context-pruning.md`, `prompt-skeleton.md`

### F. Systematic Spot-Check Sampling
- Sample a small percentage of outputs on a schedule and check against protocol
- Catches drift early and cheaply instead of in an expensive retrospective audit

### G. Protocol as Single Source of Truth for Checks
- Define MATOCP such that a validator can parse the spec and check outputs programmatically
- Protocol updates then automatically update what is enforced, rather than requiring a separate checker to be hand-updated

---

## VII-ter. Command Center Restructuring (Single Entry Point)

### A. Current State (Anti-Pattern)
The operator messages multiple agents directly. This makes the operator the de facto orchestrator, responsible for enforcing the system manually on every interaction. This is the likely structural cause of compliance drift: no component enforces anything; the operator simply remembers to.

If the operator messages agents directly, HPOM is not actually orchestrating — it is documentation of what is supposed to happen.

### B. Target State
Route all operator intent through a single orchestrating agent (HPOM, or whichever agent holds that role). Other agents receive only dispatched, protocol-shaped tasks from the orchestrator — never raw messages from the operator directly.

### C. Benefits
1. Single entry point — operator states intent once; orchestrator interprets against protocol, decomposes, dispatches
2. Centralized compliance enforcement — one component translates intent into protocol-compliant assignments before anything else touches it (a gate, not a hope)
3. Natural home for the verification layer (VII-bis.C) — check once before fan-out, not N times after
4. Matches intended architecture — converts the current hybrid into true orchestrator-worker topology

### D. Tradeoff (state honestly)
A single entry point is also a single point of failure/bottleneck. Mitigation: keep the orchestrator's job narrow and mechanical (interpret + route + validate against spec), not creative, to minimize the surface area for misinterpretation.

---

## VII-quater. Task Routing and Local-Model Utilization

### A. Problem Statement
Local agents (Ollama) sit idle because, absent explicit routing criteria, the orchestrator defaults every task to the highest-capability option. Local models are never actually offered tasks they could handle.

### B. Root Cause
- No cost/latency signal pushing work down-tier
- Every task looks "important" by default, so the weaker option loses every comparison
- No tiering: local can't win a task it was never offered

### C. Fix: Explicit Task Classification Before Dispatch
1. **Define task tiers up front**: mechanical/deterministic (formatting, boilerplate, parsing, test execution, log summarization) → local; reasoning-heavy, multi-step, ambiguous → cloud
2. **Route by task type, not by "which agent is best"**: ask "does this task *need* what only cloud provides," defaulting to local unless it fails that bar — inverts the current bias
3. **Give local a fixed lane, not open competition**: local *owns* categories (repo scans, file diffs, test runs, first-pass log triage) rather than competing for the "best agent" slot
4. **Cost/latency as an explicit routing signal**: near-zero local cost should structurally bias the router toward it within its competence range
5. **Fallback, not first-choice, for escalation**: local attempts first; escalates to cloud only on validation failure or complexity ceiling

### D. Success Metric Shift
Stop asking "would cloud have done this better" (cloud always wins). Start asking "did local resolve it within its defined lane" — a different metric entirely.

---

## VIII. Organizational Design Analogues (applied per subsystem, not system-wide)

| MAP Subsystem | Recommended Cultural Model | Mechanism to Borrow |
|---|---|---|
| HPOM (task dispatch/execution) | Lean / Toyota Production System | Andon cord, poka-yoke (mistake-proofing), kanban pull |
| emergence (idea capture) | Scandinavian flat-consensus | Low-filter, high-trust surfacing; deliberately slow |
| hcom (live coordination) | American/startup | Low-ceremony, fast, informal status reporting |
| Canonical repo / state ownership | German Mittelstand | Formal documentation, standardized procedure, zero improvisation |

**Principle**: no single organizational culture should be applied uniformly across all of MAP. Mismatched culture-to-function (e.g., applying "move fast" to canonical state ownership) is a plausible root cause of the repo drift finding.

### Real-Life Staffing Analogues (for routing and verification design)

These models all share one trait: none rely on the senior/expert resource *noticing* that junior resources exist. Each enforces routing via a role or process upstream of the work.

| Model | What It Illustrates | Applies To |
|---|---|---|
| **Hospital triage** | A triage nurse classifies severity first; minor cases go to a nurse practitioner, only complex/high-risk to the specialist. The NP owns a category, not a lesser status. | Local-model-as-first-line routing (VII-quater) |
| **Law firm associate/partner** | Associates do review/drafts/research; partners do judgment calls. Routing is enforced by billing rates and case systems — a partner personally handling everything would bankrupt the firm. | Why work defaults up-tier without a cost signal |
| **Call center tiering** | Tier 1 handles known issues off a script; escalation only for what it can't resolve. Judged on "resolved within its lane," not "could a senior have done better." | Success-metric shift for local models (VII-quater.D) |
| **Kitchen brigade / expediter** | Each station owns a responsibility; the expediter checks every plate at the pass before it leaves — no station self-reports doneness. | The verification layer (VII-bis.C) |

---

## IX. Protocol and Interoperability Considerations

### A. Current State
hcom is a bespoke coordination format. This is acceptable for a single-operator, closed system.

### B. Forward-Looking Consideration
If MAP is ever intended to interoperate with external tools or agents (not just your own), study the emerging **A2A (agent-to-agent) protocol** as the standard shape for agent messaging, and **MCP (Model Context Protocol)** for tool/context exposure — not to adopt immediately, but so that hcom's design doesn't have to be redone later if interoperability becomes a goal.

---

## X. Testing and Validation Requirements

### A. Load and Concurrency Testing
- Deliberately trigger concurrent task ID allocation, concurrent repo writes — the near-deletion incident should be reproducible in a test harness, not just known anecdotally
- Target: validate fixes at 2x expected concurrent agent load, not just 1x

### B. Adversarial / Chaos Testing
- Deliberately kill an agent mid-task, deliberately corrupt a message, deliberately introduce repo drift — confirm the system detects and recovers rather than assuming it will

### C. Regression Suite Against the MAST Taxonomy
- Each of the 14 failure modes (Section IV) should have at least one corresponding test case, even if synthetic

---

## XI. Prioritized Roadmap (Synthesis)

1. **Tier 0 (correctness, blocking)**: atomic task ID allocator, git operation lock, canonical repo decision (single vs. federated — pick deliberately)
2. **Tier 1 (structure)**: restructure command center to single entry point (VII-ter) — route all operator intent through one orchestrator; other agents receive only dispatched, protocol-shaped tasks. This is the enabling change for most fixes below.
3. **Tier 2 (compliance)**: build the separate verification layer (VII-bis.C) — the single highest-leverage compliance fix; add schema validation, compliance telemetry, and periodic protocol re-injection for instruction decay
4. **Tier 3 (visibility)**: event validator with halt authority, structured tracing across HPOM/hcom/emergence
5. **Tier 4 (routing)**: define task tiers and give local models (Ollama) a fixed lane with escalation-only fallback (VII-quater)
6. **Tier 5 (resilience)**: circuit breakers, dead-letter queues, idempotency keys on all writes
7. **Tier 6 (governance)**: pre-dispatch approval gates, capability whitelisting, escalation paths; convert operator intake checklist into an enforced gate
8. **Tier 7 (process/organizational)**: apply Section VIII culture mapping deliberately per subsystem
9. **Tier 8 (forward-looking)**: evaluate federated architecture at scale; monitor A2A/MCP standardization before any interoperability work

---

## XII. Core Reading List

1. Cemri et al., *Why Do Multi-Agent LLM Systems Fail?* (MAST-Data) — failure taxonomy
2. Anthropic, *Building Effective Agents* — orchestrator-worker reference design
3. LangGraph documentation — checkpointing and state model (concepts, not necessarily adoption)
4. Any concise primer on CAP theorem and optimistic concurrency control (distributed systems fundamentals)
5. *Team of Teams* (McChrystal) — decentralized coordination under uncertainty
6. Toyota Production System primers — andon, poka-yoke, kanban (Lean fundamentals)
7. OpenTelemetry conceptual documentation — span/trace model for observability

---

*End of outline.*
