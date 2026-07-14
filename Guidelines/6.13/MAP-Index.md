# 00 — MAP Document Index & Design Spine
### Master Index to the MAP Research & Build Series

This is the map to the whole set. The twelve documents are numbered in **implementation order**: 00–02 orient you, 03–06 are the build documents in the order you'd act on them, and 07–11 are the conceptual grounding and reference material you consult as needed. Follow the numbers and you move from understanding what MAP is, to knowing exactly what to build in what sequence, to the evidence and theory beneath it.

---

## The Two Convergent Design Principles (MAP's Evidence-Backed Spine)

Across seven independent domains — distributed systems, insect biology, microbiology, industrial logistics, coupled-oscillator physics, and hematology — two design patterns kept reappearing, each arrived at independently by fields under completely different pressures. That convergence is the strongest signal in this body of work: when unrelated systems all evolve the same solution, it points to a deep property of coordinated systems rather than a quirk of any one field.

### Principle 1: Coordinate through directly-readable shared state, not relayed messages
Agents read from and write to one authoritative, directly-observable shared surface, rather than passing status through chains of point-to-point messages that distort with each hop.
- **Supported independently by**: stigmergy (ants coordinate via marks on a shared environment), the bullwhip effect (relayed signals amplify into chaos across supply-chain layers), and Kuramoto/firefly synchronization (global coherence from observing shared local state).
- **Implication for MAP**: prioritize the single canonical shared-state design over the hcom message-passing design. This is what CRDTs, event sourcing, and the "countdown board" pattern all point at from the engineering side.

### Principle 2: Gate collective or irreversible actions behind a threshold, then respond decisively — with multiple safeguards against mis-triggering
Don't act on every individual signal. Idle beneath a threshold (absorbing noise), commit hard once a stimulus crosses a threshold in both magnitude and spread, and protect that trigger with more than one safeguard.
- **Supported independently by**: quorum sensing (bacteria act only past a density threshold), the coagulation cascade (idle on noise, amplify explosively past threshold, regulated by redundant inhibitors), and firefly coupling (synchronization locks only past a critical coupling strength).
- **Implication for MAP**: the compliance and event validators should ignore isolated noise and trigger a strong response (halt, escalate, roll back) only on correlated/widespread anomalies — behind multiple safeguards, never a single threshold check.

Everything else in the series is either engineering detail beneath these two principles, or the grounding for why they hold.

---

## The Document Series (Numbered in Implementation Order)

### 00 — MAP-Index *(this document)*
The map to everything, plus the two design principles that form MAP's spine.

### 01 — MAP-Thesis
The central reframe: MAP is a coordination system that happens to use AI workers, not an AI system. Its failures are management and distributed-systems failures with names in older disciplines. **Read this first** to understand what MAP fundamentally is in ten minutes.

### 02 — MAP-Implementation-Roadmap
The capstone build plan. Reconciles every document's local roadmap into one dependency-ordered sequence of seven phases (correct state → single entry point → visibility → enforcement → intelligence → resilience → governance). **This is the spine of the whole build** — includes the critical-path diagram and a "Minimum Viable MAP" if you only do a fraction. Read after the thesis to see the shape of the work.

### 03 — MAP-System-Requirements-Outline
The core engineering document. A twelve-section academic outline of everything MAP needs — distributed-systems foundations, architecture patterns, failure taxonomy, observability, reliability, governance, compliance enforcement, command-center restructuring, task routing — with a Tier 0–8 roadmap. The detailed "what to build" that the roadmap sequences.

### 04 — MAP-Formal-Verification
The TLA+ path for proving (not just testing) MAP's hardest invariants — the atomic allocator, the git lock, canonical-state consistency. Scoped narrowly: a weekend on the two or three hardest concurrency problems, not the whole system. Belongs to Phase 0 of the roadmap.

### 05 — MAP-Organizational-Model
The in-depth, cherry-picked hybrid of business/structure models — Jidoka (Lean) for the execution layer, Team Topologies as the backbone (cognitive load as the routing principle), the Spotify alignment/autonomy matrix and blast-radius containment, and the Mittelstand/Six-Sigma anchor for state ownership. Provides the Phase-1 structural backbone and the Phase-4 routing logic.

### 06 — MAP-Emergence-Design
The design for the emerge/instinct subsystem: outward (inferring unstated requirements) and inward (finding its own weak points and self-improving, both as-we-go via Reflexion and end-of-day via experiential memory). MAP's defense against under-specification, the single most common multi-agent failure mode. Phase 4 of the roadmap.

### 07 — MAP-Philosophical-Foundations
Six thinkers underpinning the design — Wiener (cybernetics), Beer (Viable System Model), Ashby (requisite variety), Hayek (the knowledge problem), Wittgenstein (rule-following paradox), Polanyi (tacit knowledge) — with primary works and a reading priority. The conceptual grounding for *why* the design principles hold.

### 08 — MAP-Cross-Domain-Research
Volume I of the verified cross-domain sources: CRDTs (the real engineering behind the "entanglement" metaphor), Artificial Immune Systems (self/non-self detection), and Braess's Paradox (why adding infrastructure can backfire). Separates rigorous research from evocative metaphor.

### 09 — MAP-Cross-Domain-Research-II
Volume II: stigmergy (ant coordination), quorum sensing (bacterial threshold action), and the bullwhip effect (signal amplification in layered systems). Where the two convergent principles first became visible.

### 10 — MAP-Cross-Domain-Research-III
Volume III: firefly/Kuramoto synchronization (decentralized timing) and the blood coagulation cascade (threshold-gated response to signal vs. noise). Both already ported into distributed computing; the point where both patterns became firmly established.

### 11 — MAP-Lessons-Learned
The stress-test document. For each research area, what actually *failed* in practice and the specific caution for MAP — convergence-isn't-correctness (CRDTs), the false-positive ceiling (immune systems), intervention-backfire (Braess). Consult before adopting any cross-domain idea.

---

## How the Pieces Fit

- **01 Thesis** says what MAP is.
- **02 Roadmap** says what to build and in what order.
- **03 Requirements** says what each piece is in detail.
- **04 Formal Verification, 05 Organizational Model, 06 Emergence** are the deep designs for the hardest/most distinctive subsystems.
- **07 Philosophy** says why the design principles hold conceptually.
- **08–10 Cross-Domain Research** give independent real-world evidence for the two principles and concrete mechanisms to borrow.
- **11 Lessons Learned** guards against adopting any of it naively.

The through-line: MAP's hardest problems are old problems that many independent systems — engineered and evolved — have already solved. The work is translation, not invention.

---

## Method Note (Worth Preserving)

The cross-domain volumes were produced by a deliberate, repeatable method, not free association:
1. **Find** a distant domain that faced MAP's structural problem under different survival pressure.
2. **Verify** it's real, citable research — not just an appealing metaphor.
3. **Stress-test** it by asking what failed in that domain and what the corresponding caution is for MAP.

This find → verify → stress-test method is itself an asset — it's what distinguishes this body of work from the framework-comparison material that dominates the space, almost none of which shows evidence of cross-domain sourcing.

---

*Index to the MAP research & build series. Twelve documents, numbered in implementation order.*
