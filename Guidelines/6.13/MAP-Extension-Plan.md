# MAP Extension Plan: Six Missing Components
### What They Are, and How to Build Each One Into the Existing System

Six capabilities the synthesized system doesn't address but mature systems have. This plan specifies each concretely — tied to the primitives MAP already has (the WAL-mode SQLite event store, the `filelock` cross-process lock, the shared-state board, the three-tier roster, idempotency keys) — so each is an extension of existing structure, not a new subsystem bolted on.

They split into two kinds:
- **Architectural (belongs in core):** Cost Governance, Outcome Feedback. These change what MAP fundamentally is and should be treated as first-class components.
- **Distributed-systems hygiene:** Dependency DAG, Durable Execution, Heartbeats, Degradation Policy. Standard, well-understood, needed once MAP runs real workloads — but not identity-defining.

Each section: **What it is → Why MAP needs it → How to build it → Dependencies → Effort.**

---

## 1. Cost Governance (ARCHITECTURAL — highest priority)

**What it is.** A spend governor: per-task and per-day token budgets, a cost-based circuit breaker (trips on spend, not failure), and a hard kill-switch. The one omission that can cost real money.

**Why MAP needs it.** MAP burns real dollars through the paid Claude tiers. Nothing currently caps spend — an emergence loop that keeps re-inferring, or a validator↔agent retry cycle that doesn't converge, could run up a serious bill before you notice. Every production agent framework treats budgets and a runaway kill-switch as first-class.

**How to build it.**
1. **Token accounting on the event log (you already have the store).** Extend the event schema with `tokens_in`, `tokens_out`, `tier`, and a computed `cost` per agent call. The three tiers carry different rates — reasoning expensive, cheap-language cheap, local ~free — so cost is `tokens × tier_rate`.
2. **Running counters, checked at the dispatch point (Phase 1's single entry point).** The orchestrator maintains a per-task cost sum and a per-day cost sum (both just `SELECT SUM(cost)` queries against the event log, or cached counters). Before dispatching any subtask, check both.
3. **Two thresholds, two responses.**
   - *Per-task budget exceeded* → halt that task, escalate to operator ("TASK-042 hit its 50k-token budget; continue / abort?"). This catches a single runaway task.
   - *Per-day budget exceeded* → the orchestrator stops dispatching new work entirely and notifies you. This caps total exposure.
4. **Cost circuit breaker — distinct from the failure breaker (Round 4).** Trips on *spend rate* (e.g. tokens/minute above a ceiling), catching a fast-burning loop even before it hits the absolute budget.
5. **Kill-switch.** A `filelock`-guarded flag file (`map_halt.flag`). If present, the orchestrator halts all dispatch immediately on its next check. You (or an automated monitor) can drop that file to stop everything instantly.

**Dependencies.** The event store (for accounting) and the single entry point (for the checkpoint). Both are early-phase, so this can land early.

**Effort.** Low. It's counters plus a check at one chokepoint plus a flag file. High value per line.

---

## 2. Outcome Feedback (ARCHITECTURAL — highest priority, the anti-gaming mechanism)

**What it is.** A feedback channel where the *real-world result* of a completed task (it actually worked / it didn't) flows back as a distinct, **higher-authority signal than validation**. Validation checks whether output *passes*; outcome checks whether it was *actually good in use*.

**Why MAP needs it.** This is the deepest gap. The validator checks output at production time; emergence's learning trains on those validation signals. But there's a gap between "passed validation" and "worked when you ran Pathwell." If emergence learns only from validation, **it can get very good at passing its own checks while drifting from actual usefulness** — the reward-hacking / online-evaluation problem. Reality has to be the higher authority, or the self-improving apparatus optimizes toward gaming itself.

**How to build it.**
1. **A distinct outcome event type.** Separate from `validation_pass`. An outcome is recorded later — by you marking a shipped task worked/didn't, or by an automated real-world check (e.g. the feature's own test run in Pathwell days later). Outcomes are sparse and authoritative; validations are frequent and fallible.
2. **Two-tier signal, weighted.** Emergence's learning (Round 5) weights `outcome_confirmed` **above** `validation_pass`. A task that passed validation but failed in reality is a strong negative signal *and* a specific flag that the validator has a blind spot.
3. **The divergence is itself a tracked metric — the validator blind-spot rate.** Every "passed validation, failed in reality" event is logged as a validator miss. That rate directly measures the thing the Validator Spec flagged as unmeasured (the real false-*negative* rate), and it's the signal that tells you where to add deterministic checks (Layer 1) or tune the judge (Layer 2).
4. **Closes the loop against gaming.** Because reality outranks validation, the system cannot improve its scores merely by satisfying its own checks — divergence between the two is caught and penalized.

**Dependencies.** Emergence (the learner), the validator (the thing being graded), and the event store (to record outcomes and compute divergence). Lands after those exist.

**Effort.** Medium. The channel and event type are simple; the value is in wiring the weighting into emergence and surfacing the blind-spot rate.

---

## 3. Dependency DAG / Task Ordering (hygiene — high, ties to the decomposer)

**What it is.** Tasks as a directed acyclic graph with topological ordering — subtask B declares it needs A's output, so B can't start until A lands. Determines what runs in parallel vs. what waits.

**Why MAP needs it.** The design discusses *decomposition* but never *dependency resolution*. Without it, the orchestrator either over-serializes (everything sequential, slow) or dispatches tasks whose inputs don't exist yet (defects). This is the core job of every workflow engine (Airflow, Dagster, Temporal, Prefect).

**How to build it.**
1. **The decomposer emits dependency edges.** When HPOM decomposes intent into subtasks, each subtask carries a `depends_on: [ids]` list. (This also sharpens the decomposer black box — it forces the decomposition to be explicit about ordering.)
2. **Store edges in the `causal_edges` table you already have.** It was introduced for tracing, but dependency edges fit the identical structure — one table, two edge types.
3. **Ready-set dispatch.** A subtask is "ready" only when every `depends_on` entry is `done`. The orchestrator dispatches all ready tasks at once (natural parallelism) and holds blocked ones. As each task completes, re-evaluate the ready set.
4. **Cycle detection at decomposition time.** A dependency cycle is a decomposer bug — reject it before dispatch. This is a natural extension of `validate_task_graph.py`: add an acyclicity check and a dependency-resolvability check to what it already validates.

**Dependencies.** The decomposer (to emit edges) and `validate_task_graph.py` (to check them). 

**Effort.** Medium. Topological ordering is standard; the work is making the decomposer declare dependencies and extending the validator.

---

## 4. Durable / Resumable Execution (hygiene — medium, heaviest to build)

**What it is.** In-progress work checkpointed so a task that dies partway (agent crash, machine reboot, power loss) **resumes from where it left off** rather than restarting from zero.

**Why MAP needs it.** MAP currently checkpoints *state* (the event log) but not *in-progress work*. For multi-step tasks that take real time, restart-from-scratch is expensive and sometimes non-idempotent. This is Temporal's core idea, which was name-checked early but never incorporated.

**How to build it.**
1. **Checkpointable steps.** Break long tasks into discrete steps. Each completed step writes its result plus a `step N done` marker to the event log *before* the next step begins.
2. **Resume on restart via event replay.** On startup, the orchestrator scans for tasks in `in_progress` state, finds the last `step N done` marker, and resumes from step N+1. This is event-sourcing replay applied to execution — and it reuses the event store you already have.
3. **Reuses idempotency keys (Round 4).** Because steps carry idempotency keys, re-running a partially-completed step is safe — which is what makes resume-from-middle correct rather than corrupting.

**Dependencies.** The event store (for checkpoints) and idempotency keys (for safe resume). Both exist by mid-roadmap.

**Effort.** High — and only worth it for genuinely long multi-step tasks. For short tasks, the dead-letter-queue retry (already built) is sufficient; don't over-invest here until task duration justifies it.

---

## 5. Heartbeats / Liveness Detection (hygiene — medium, cheap)

**What it is.** Detection of a *hung* agent (as opposed to a *failing* one). A wedged local model or stuck process doesn't fail — it goes silent — and nothing currently notices.

**Why MAP needs it.** The circuit breaker (Round 4) handles *persistent failure*, but not *silence*. These are different failure modes needing different detection. Every distributed system has liveness probes (Kubernetes' are canonical).

**How to build it.**
1. **Agents heartbeat to the shared board (you already have it).** While working, each agent periodically writes a `last_seen` timestamp to its slot on the shared-state board (the observability countdown board).
2. **A reaper in the orchestrator.** Periodically scan for tasks whose agent's `last_seen` is older than a timeout. A stale heartbeat → reclaim the task (re-queue via dead-letter) and mark the agent suspect.
3. **Feeds the circuit breaker.** Repeated reaping of one agent's tasks counts toward the breaker's failure streak — so a chronically-hanging agent eventually gets pulled from rotation, unifying the "silent" and "failing" signals.

**Dependencies.** The shared board (heartbeat target) and the dead-letter queue (to reclaim). Both exist by mid-roadmap.

**Effort.** Low. A timestamp write and a periodic scan.

---

## 6. Degradation / Fallback Policy (hygiene — medium, mostly decisions)

**What it is.** Explicit, pre-decided behavior for when a dependency is unavailable — fail-open vs. fail-closed, made *in advance* rather than discovered during an outage.

**Why MAP needs it.** MAP has resilience *mechanisms* but no stated degradation *policy*. When cloud is down, does it fall back to local or stall? When the validator is down, does it ship unchecked (fail open) or halt (fail closed)? These are safety-relevant decisions that shouldn't be discovered mid-incident.

**How to build it.** This is mostly a **decision table**, defined once and enforced at the dispatch point:

| Dependency unavailable | Policy | Rationale |
|---|---|---|
| **Cloud tier** | Fall back to local-only for eligible tasks; queue the rest; notify operator | Keeps mechanical work flowing; defers what needs reasoning |
| **Validator** | **Fail CLOSED — halt, do not ship unchecked** | Safety-critical: unchecked output is the failure mode MAP exists to prevent |
| **Canonical store (locked/unavailable)** | Block writes; allow reads from last snapshot | Preserves progress visibility without risking corruption |
| **Local model (OOM/crash)** | Fall back to cloud (note the cost implication → ties to Cost Governance) | Keeps work flowing; budget governor catches the cost |
| **Operator absent (for an approval gate)** | Hold the gated action; proceed with un-gated work | Never auto-approve an irreversible action; don't stall everything else |

The one decision to make deliberately and never soften: **the validator fails closed.** Everything else optimizes for continued progress; the validator optimizes for safety.

**Dependencies.** The mechanisms it governs (tiers, validator, store, gates) must exist to be governed. Define the table early; enforce each row as its mechanism lands.

**Effort.** Low code, but requires deliberate decisions. The table above is a starting point to adjust.

---

## Integrated Build Sequence

Slotting the six into the existing seven-phase roadmap (from the synthesized doc):

- **Phase 1 (single entry point):** add **Cost Governance** counters + kill-switch (chokepoint already exists) and the **Degradation Policy** table (define it now).
- **Phase 2 (observability):** add **Heartbeats** (the board already exists) — near-free here.
- **Phase 3–4 (validator, emergence, decomposer):** add the **Dependency DAG** (extend `validate_task_graph.py` + decomposer) and, once emergence + validator exist, **Outcome Feedback** (the architectural anti-gaming loop).
- **Phase 5 (resilience):** add **Durable Execution** (reuses idempotency + event store) — but only if task durations justify the effort.

**Priority order if building incrementally:**
1. **Cost Governance** — real-money risk, cheap, early. Do first.
2. **Degradation Policy** — a decision table; cheap, prevents mid-incident scrambling. Do early.
3. **Heartbeats** — near-free once the board exists.
4. **Dependency DAG** — correctness-critical once tasks have real interdependencies.
5. **Outcome Feedback** — architectural and high-value, but depends on emergence + validator being real first.
6. **Durable Execution** — heaviest; defer until long multi-step tasks make it pay.

---

## The Two That Change What MAP Is

Four of these are hygiene — MAP will want them, but they don't alter its character. **Two are architectural and belong in the core identity of the system:**

- **Cost Governance** makes MAP *economically bounded* — a system that cannot run away with your money is fundamentally different from one that can.
- **Outcome Feedback** makes MAP *honestly self-improving* — a system graded by reality can't game its own checks, which is the difference between one that genuinely gets better and one that merely gets better at looking better. This is the single most important addition on the list, because it protects the integrity of the entire self-improvement apparatus that so much of the design rests on.

Everything else keeps MAP running smoothly. These two keep it *honest and safe* — which is why they warrant promotion into the synthesized system itself, not just the extension backlog.

---

*Companion to MAP-The-Synthesized-System.md and MAP-Gap-Register.md. Cost Governance and Outcome Feedback are candidates for promotion into the core system; the other four are the distributed-systems hygiene layer.*
