# MAP Gap Register
### What's Tested, What's Assumed, and What's Untouched

The synthesized system and five simulation rounds are polished enough to *imply* a completeness they don't have. This document exists to counter that — an honest, standing account of the holes. It sorts everything into three buckets: **validated** (tested, evidence exists), **assumed** (the system depends on it but it was taken as given), and **untouched** (never addressed at all). Read this before trusting the system's apparent thoroughness.

The governing honesty: **every result so far came from a model of MAP, not MAP.** The directions are robust across seeds and stress tests; none of them touched the real repository. That single fact reframes everything below.

---

## Bucket 1 — VALIDATED (tested, with evidence)

These have real simulation evidence behind them and can be relied on *within the model's assumptions*:

- **Coordination via shared state, not messages** — zero point-to-point messages needed (Round 1).
- **Atomic allocation prevents collisions** — but only when the lock is cross-process (Round 2 found 599/600 collisions unlocked).
- **Eager halting beats threshold gating** — 100% vs 47% catch, robust to 4× cost (Rounds 1–2).
- **Validator accuracy, not threshold, preserves trust** — ~1% false-positive target (Round 2).
- **The knowledge/Library layer pays off — but only in full** — staleness tracking is load-bearing; summaries-only is worse than no library (Round 3).
- **The resilience layer, all four mechanisms** — blast-radius, dead-letter, idempotency, circuit breaker, each owning a failure mode (Round 4).
- **The learning loop converges but needs a pruning guard** against endogenous over-learning (Round 5).
- **Four mechanisms correctly cut** — threshold gating, strict routing, pre-tokenization, peer review (Rounds 1, 3).

**The caveat on all of it:** validated *against assumed parameters*. See Bucket 3, item 1.

---

## Bucket 2 — ASSUMED (the system leans on these, but they were taken as given)

These were treated as solved in every simulation. They are not solved — they were *stipulated*. Each is a real design problem still open.

### 2a. The validator is a black box — and it's the hardest component
Every round assumed "the validator catches real defects at ~1% false positives." **How it actually distinguishes a genuine defect from correct-but-unusual output was never specified.** The entire eager-halt conclusion — the biggest correction in the whole effort — rests on an accuracy number that was asserted, not designed. This is the single most important open component: schema-checking is easy, but semantic correctness-checking (did this output actually do the right thing?) is unsolved here. Until the validator is specified and its real false-positive rate measured, the eager-halt policy is a hypothesis.

### 2b. The orchestrator's decomposition is also a black box
"HPOM interprets intent and decomposes it into subtasks" was never modeled. Routing, allocation, and validation were all tested *downstream* of decomposition — but if decomposition is wrong, every downstream mechanism inherits the error and none of them would catch it. How intent becomes a correct set of subtasks is unspecified and untested.

### 2c. Emergence's inference quality
The simulations modeled emergence's *dynamics* (convergence, over-learning) but assumed it can actually infer the right missing capabilities. The real ~50% F1 ceiling from the requirements-engineering literature (noted in the design docs) was never simulated. How good the inference truly is, on real tasks, is unmeasured.

### 2d. The parameters themselves
The 8:1 shipped-defect-to-false-halt cost ratio, 10× compression, local-vs-cloud skill gap, file churn rate — all assumed. They drove every decision. They are guesses until measured (Bucket 3, item 1).

---

## Bucket 3 — UNTOUCHED (never addressed)

### 1. Calibration against the real repo — THE highest-value gap
Nothing tested touched the actual MultiAgentProject. The most valuable next action is not more simulation — it's **measuring the four driving parameters on the real system** (real shipped-defect vs false-halt cost, real local-vs-cloud defect rates, real file churn, real compression ratio) and re-running. Everything so far is "the design is sound"; nothing yet is "the design works *here*." If the real numbers differ sharply from the assumed ones, specific conclusions could shift — most sensitively the eager-halt threshold (robust to 4× cost, but not tested against a regime where false halts are catastrophic in a way tokens don't capture).

### 2. Recovery from a *committed* poisoned state
Round 4 tested *containing* corruption before it spreads. It never tested what happens when bad state gets **committed to canonical state before detection** — how you detect it after the fact, roll back, and reconcile. This is the actual aftermath of the near-deletion incident, and it's the scenario most likely to recur in practice. Untested.

### 3. Latency / wall-clock time
Every cost was measured in tokens or work-units. **Never in wall-clock time.** A system can be token-cheap and painfully slow. Whether the single-entry-point orchestrator becomes a throughput bottleneck under real concurrent load, and how long a task actually takes end-to-end, are unknown. The single-entry-point design's main risk (a bottleneck) was never measured.

### 4. Security and trust boundaries
Agents have file, repo, and shell access; a compression proxy would read everything; MCP connectors reach external services. **No threat model exists.** What a misbehaving, buggy, or compromised agent can actually reach — and what damage it could do to canonical state or the host — was flagged once about third-party repos and never returned to. This is a real hole for a system with real filesystem access.

### 5. Human factors — the operator as a finite, sometimes-absent bottleneck
The whole system routes through one operator (you). Operator interrupts were modeled as a *number*, but never as a real constraint: total attention load across emergence suggestions + governance approvals + validator escalations, what happens when you're **not there**, and whether the system can make safe progress unattended or stalls waiting for approval. The system's dependence on human availability is unquantified.

### 6. Cold start and migration
Every simulation began in a clean steady state. **How MAP gets from your current drifted, two-copy repo to the tuned design was never addressed.** The transition — the flag-day risk, migrating live state, resolving the existing drift — is where real systems break, and it's entirely unmodeled.

### 7. Multi-project reality
MAP is reusable across projects (Pathwell and others). Every test modeled a single project. **Shared MAP state across projects, cross-project resource contention, per-project isolation** — untouched. The reusable-system claim was never stress-tested against actual multi-project use.

### 8. The three-tier roster composition
Flagged as untested at the end of Round 5 and still is. Whether the cheap-language tier actually earns its slot (vs. a two-tier reasoning/local split), and the optimal agent count per tier, were never simulated. A Braess-style question left open.

---

## The Meta-Hole (the honest one)

**The simulations kept confirming the design partly because the same mental model built both the design and the tests.** Nothing here was adversarial in the deepest sense — no independent party tried to break the *assumptions*, only the parameters within them. The convergence across five rounds is real, but partly self-referential. The three times a test initially masked a failure (the GIL race, the circuit breaker, the spurious-heuristic guard) hint at how much *else* a differently-framed test might surface. A genuinely external red-team of the assumptions — not the parameters — is the deepest missing check.

---

## Prioritized: What to Actually Do About the Holes

Ranked by value, and notably **none of the top items are "more simulation"**:

1. **Calibrate the four driving parameters against the real repo** (Bucket 3.1). Turns "sound in theory" into "works here." Highest value, because it validates or invalidates everything else.
2. **Specify and measure the validator** (Bucket 2a). The hardest component and the one the biggest conclusion rests on. Real design work, not simulation.
3. **Specify the decomposer** (Bucket 2b). The other black box; upstream of everything.
4. **Design committed-state recovery** (Bucket 3.2). The near-deletion aftermath; most likely real-world failure.
5. **Write a threat model** (Bucket 3.4). Before agents get real filesystem/shell access in anger.
6. **Measure operator load and unattended behavior** (Bucket 3.5). The human bottleneck.
7. **Plan the migration** from the current drifted repo (Bucket 3.6). Before any of the rest ships.
8. **Simulate the roster composition** (Bucket 3.8) — the one remaining item that *is* just another simulation round.

---

## The One-Sentence Honest Summary

The synthesized system is well-reasoned and, within its assumptions, well-tested — but its two hardest components (the validator and the decomposer) are unspecified black boxes, every number is a guess until measured against the real repo, and entire categories (latency, security, human availability, migration, multi-project) were never touched; the polish should not be mistaken for completeness.

---

*Companion to MAP-The-Synthesized-System.md and the five simulation-results documents. This register is deliberately the least flattering document in the set, and the most important for staying honest about what is and isn't known.*
