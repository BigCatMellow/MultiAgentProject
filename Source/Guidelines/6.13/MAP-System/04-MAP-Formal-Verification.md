# MAP Formal Verification: The TLA+ Path
### Proving MAP's Core Invariants Instead of Reasoning About Them by Hand

This document covers how formal methods — specifically TLA+ — apply to MAP's hardest correctness problems (the P0 invariants: atomic task-ID allocation, the git operation lock, and canonical-state consistency). It is scoped deliberately: TLA+ is a tool for **proving the design of the two or three hardest concurrency problems**, not for specifying all of MAP. Treat it as a precision instrument for the incidents that manual reasoning and testing can't reliably catch.

---

## 1. What TLA+ Is and Why It Fits Here

TLA+ (Temporal Logic of Actions) is Leslie Lamport's formal specification language for concurrent and distributed systems. It combines temporal logic, first-order predicate logic, and set theory into one language for describing what a system should do as logical formulas, which a model checker then verifies exhaustively.

The useful mental model: TLA+ is **exhaustively-testable pseudocode**. You write the *design* of a protocol as a state machine, state the properties it must never violate, and the **TLC model checker** explores every reachable state (up to a bound) looking for a violation. If it finds one, it returns the exact step-by-step trace that produces it.

Why it fits MAP specifically: the failures TLA+ is built to catch are precisely MAP's failure class — race conditions that manifest once per million requests, deadlocks that occur only under specific failure sequences, and data corruption from unexpected state interleaving. The near-deletion incident was exactly this kind of bug: an interleaving that normal testing didn't surface.

---

## 2. The Core Formula Shape

A TLA+ specification has the form:

```
Spec == Init /\ [][Next]_vars /\ Liveness
```

Read as: *start in a valid initial state (Init), AND every step is a legal transition (Next), where `[]` means "always", AND good things eventually happen (Liveness).*

Properties come in two kinds, checked differently:
- **Safety** ("nothing bad ever happens") — invariants checked against every reachable state. For safety, TLC explores all reachable states looking for one where an invariant fails or deadlock occurs. This is the bulk of what MAP needs.
- **Liveness** ("something good eventually happens") — checked with fairness conditions. Most specifications don't need liveness; safety often suffices.

---

## 3. MAP's P0 Invariants as TLA+ Properties

Each MAP P0 maps to a standard, well-studied safety property:

| MAP problem | TLA+ property | Canonical name |
|---|---|---|
| Git operation lock | At most one agent holds the write-lock in any state | Mutual exclusion |
| Atomic task-ID allocator | No two tasks ever share an ID | Uniqueness invariant / resource allocation |
| Near-deletion incident | When an agent terminates, it holds no locks | Orphan-lock freedom |
| System never wedges | There is always a possible next step | Deadlock freedom |
| Eventual cleanup | Every claimed task is eventually released | Liveness (fairness) |

The value: instead of *believing* the atomic allocator fixes the race, TLC can **prove** no reachable state has two tasks sharing an ID — or hand back the precise interleaving that still breaks it, so a fix can be confirmed to actually close the hole.

---

## 4. This Is Not Academic — Direct Precedent

Two pieces of evidence that this transfers to MAP rather than staying theoretical:

- **Industrial use**: AWS has used TLA+ since 2011 on DynamoDB, S3, and Elastic Block Store; Microsoft has applied it to Cosmos DB. AWS engineers reported it caught subtle bugs that would have been extremely difficult to find through code review or testing.
- **Direct agent-coordination precedent (2026)**: the **TraceFix** paper (arXiv:2605.07935) applies TLA+ to *agent coordination protocols specifically*, checking mutual exclusion for locks, orphan-lock freedom on termination, channel drainage, and deadlock freedom — and explicitly frames its property choice around the MAST taxonomy, noting that specification and orchestration gaps are the dominant multi-agent failure mode. This is MAP's exact problem set, already formalized by someone else.

---

## 5. Essential Repositories

### Toolchain (start here)
- **tlaplus/vscode-tlaplus** — TLA+ language support for VS Code; runs the TLC model checker from the editor. The practical entry point, better suited to this workflow than the older standalone Toolbox.

### The specification library to clone
- **tlaplus/Examples** (~1.5k stars, MIT license) — the official corpus. Three specs map directly onto MAP:
  - **dijkstra-mutex** / **lamport_mutex** — the classic mutual-exclusion algorithms, formally specified. This *is* the git-lock problem in canonical form.
  - **allocator** (by Stephan Merz) — a resource-allocator spec; the abstract version of the task-ID allocator.
  - **transaction_commit/TwoPhase.tla** — two-phase commit ("all parties commit or all abort"); relevant if MAP goes the federated-repo route with sync contracts.
  - **DieHard** — the movie water-jug puzzle; the standard "first TLA+ spec," best starting point for intuition.

### Learning path
- **tlaplus/DrTLAPlus** (~858 stars) — the "Dr. TLA+" series, walking through one algorithm/protocol at a time. More structured for learning than reading raw specs.
- **miguelmota/tla-learning** / **cs6213/tlaplus-examples** — smaller, gentler notes-and-basics repos for the first day.

### The frontier (the bridge to MAP's real gap)
- **tlaplus/awesome-tlaplus** — the curated meta-list. Contains entries on **using TLA+ specs as prompts for AI agent-mode code generation** and **generating implementations from TLA+ specs using LLMs via stepwise refinement**. This is the bridge across TLA+'s main limitation (see §6) — turning a verified design into verified code — and it's being actively built right now.
- Production specs worth reading as models (from the awesome list): MongoDB replication, Kafka ISR replication (model checking revealed weaknesses in proposed designs), Microsoft CCF/Raft. One real spec that caught an actual data-loss bug teaches more than a dozen toy examples.

---

## 6. The Honest Limits

Three real constraints, so this is adopted with eyes open:

1. **State-space explosion.** TLC explores all interleavings, so the state space can grow exponentially with the number of variables and processes; specs often need abstraction or symmetry reduction to stay tractable. Practical consequence: model a small abstract version (2–3 agents), not the full system. Simulation mode (random walks) can find bugs in minutes when exhaustive checking would take hours.
2. **Design ≠ implementation.** A verified TLA+ spec proves the *design* is correct; it does not prove your Python matches that design. Trace-validation tooling (and the LLM-transpilation work in §5) is closing this gap, but it remains the main caveat.
3. **Not everything is covered.** Even the agent-focused TraceFix is explicit that its mutual-exclusion check doesn't fully cover livelock and starvation. TLA+ proves what you state; it can't prove properties you didn't think to write.

---

## 7. The Narrow, High-Value Path for MAP

Do **not** try to specify all of MAP in TLA+. The focused, weekend-sized move:

1. Install the **vscode-tlaplus** plugin.
2. Clone **tlaplus/Examples**; open **DieHard** to learn the syntax, then **allocator** and **dijkstra-mutex** as templates.
3. Write one small spec of MAP's task-ID-allocator-plus-lock, with 2–3 abstract agents.
4. State the three safety invariants from §3 (mutual exclusion, ID uniqueness, orphan-lock freedom).
5. Run TLC. Either it verifies the design is race-free within those bounds, or it reproduces the near-deletion interleaving precisely — before you commit to a fix.

This is the formal-methods expression of the andon-cord / poka-yoke instinct from the Lean discussion: make the failure *structurally impossible* and prove it, rather than catching it after the fact. It targets the specific incident that motivated MAP's audit, at a cost of a weekend rather than a rewrite.

---

## 8. Connection to the Rest of the Series
- **Requirements Outline** (Tier 0): the P0 fixes this verifies are the top of the roadmap; TLA+ is how you confirm they actually work, not just that they were written.
- **Principle 2** (threshold-gated, safeguarded action): formal proof is the strongest possible safeguard on the most critical invariants.
- **Lessons Learned** (convergence ≠ correctness): TLA+ checks *correctness of the design*, complementing runtime validators that check *correctness of a given execution* — two different guarantees, both needed.
- **Logic lineage**: this is the concrete payoff of the "formula for logic" thread — temporal logic over first-order predicates, made executable via TLC.

---

*Companion document to the MAP series. Extends the Tier 0 correctness work in MAP-System-Requirements-Outline.md.*
