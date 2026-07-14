# MAP Simulation Results: The Tuned Machine
### What Survived Contact With the Data — and What Got Thrown Overboard

This document reports the outcome of actually building and running MAP as a simulation, iterating across four versions, and letting measured cost drive every decision rather than the design docs. The instruction was explicit: hold onto nothing for its own sake; if a structure makes things worse, cut it. Several pieces of the design series did make things worse. They were cut.

Every claim here is backed by a run in the harness (`map_v1.py` through `map_v4.py`), across 5–8 random seeds each for stability.

---

## Headline

The design series specified an elaborate coordination system. **The data drove it toward a dramatically simpler machine that outperforms the elaborate one.** Three named mechanisms from the design docs turned out to be net-negative in simulation and were removed. The final config holds a **100% defect catch rate even under 2× load with degraded agents**, at lower total cost than any version with the extra mechanisms.

The recurring lesson, seen three separate times: **adding a plausible-sounding mechanism made the system worse.** This is Braess's Paradox from the Lessons-Learned document, observed live and repeatedly in MAP's own simulation.

---

## What Was KEPT (earned its place in the data)

| Mechanism | Why it survived |
|---|---|
| **Single entry point (HPOM)** | Never a cost problem; the structural backbone everything else needs. |
| **Atomic task-ID allocation** | Zero ID collisions across every run. The Phase-0 fix works exactly as designed. |
| **Git lock / mutual exclusion** | Zero lock violations across every run. Works as designed. |
| **Coordination via shared state, not messages** | Zero point-to-point messages needed; agents stayed consistent by reading shared state. Principle 1 confirmed. |
| **Cognitive-load routing (local vs cloud)** | Kept — but see "strict routing" below; the *basic* split is fine, the elaboration was not. |
| **Emergence gap-scoring + inference** | Kept, but required recalibration (see Fixes). The core idea works; one parameter was badly wrong. |
| **Validator with halt authority** | Kept — but the *threshold* was removed (see Cuts). Halt authority itself is essential. |
| **End-of-day learning** | Kept; low-cost, and it removes recurring defect classes over time. |
| **Structured event log** | Kept; near-zero cost, and it's what makes all of this measurable. |

---

## What Was CUT (made the system worse, or added nothing)

### 1. Threshold gating on the validator — CUT (this was the biggest finding)
The design series leaned heavily on Principle 2: idle on isolated noise, act only on correlated signals crossing a threshold — drawn from quorum sensing and the coagulation cascade. **In simulation this was actively harmful.**

- threshold=1: **100% catch rate**, total cost **737**
- threshold=2: 47% catch rate, 47 defects shipped, cost **1020**
- threshold=3: 28% catch rate, 63 defects shipped, cost **1060**

Why the biological analogy failed here: a biological system's "noise" genuinely is noise, but **a software defect's first occurrence is already a real defect worth catching.** Waiting for a second correlated signal just ships the first one. The threshold was solving a problem MAP doesn't have. Cost of a shipped defect (found late) dwarfs the cost of a false halt, so the correct policy is to halt eagerly. **Threshold removed; validator halts on first raised signal.**

*This is the clearest example of the instruction in action: a well-grounded, elegant, biologically-validated mechanism was cut because the data said it hurt.*

### 2. "Strict routing" (force hard caps to cloud always) — CUT
Hypothesis: routing reasoning-heavy work exclusively to higher-skill cloud agents would reduce defects. **Data: no effect whatsoever** (cost 737 → 737). Once the validator catches everything at threshold=1, where a defect originated is irrelevant to shipped count, and the routing constraint didn't improve throughput either. A plausible lever that does nothing. Removed.

### 3. Pre-defining tokenization rules in emergence — CUT
Hypothesis: having emergence force-include tokenization rules on every text task would eliminate the under-specification defect class at the source. **Data: made things worse** (737 → 814). It adds a capability (and subtasks, and work) to every text task, while the validator was already catching those defects anyway. Paying up front to prevent something you already catch cheaply downstream is net-negative. Removed.

### 4. Peer review — CUT (survived one round, then failed a fair test)
This is the subtlest one and the best illustration of why realistic modeling matters. In v3, peer review looked like the single best lever (−18% cost). But v3 let the reviewer fire *only when a defect actually existed* — which is cheating, because in reality **you don't know which outputs are defective in advance.**

When modeled realistically in v4 (review a fixed fraction of *all* outputs, paying the cost every time):
- review_rate 0.0: cost **664**
- review_rate 0.25: cost 675
- review_rate 0.50: cost 693
- review_rate 1.00: cost 728

Cost rises monotonically with review. With the validator already at 100% catch, peer review is redundant paid work. **Removed.** The v3 result was an artifact of an unrealistic assumption — a caution worth remembering for any future lever.

---

## Fixes Applied (kept the mechanism, corrected the parameter)

### Emergence confidence recalibration — operator interrupts 83 → 28
v1 pestered the operator on ~83% of tasks. Diagnosis pinpointed a single cause: **`edge_cases` was classified low-confidence, and alone generated ~65% of all interrupts.** It's a routine capability for most features, not a judgment call. Reclassifying it (and similar routine caps) as high-confidence auto-add dropped interrupts to ~28 with no loss in catch rate. One miscalibrated parameter was causing two-thirds of the operator friction.

---

## The Final Tuned Configuration

```
ENTRY POINT
  Single orchestrator (HPOM). All intent enters here. [KEPT]

STATE
  One canonical store.
  Atomic task-ID allocation.            [KEPT — 0 collisions]
  Mutual-exclusion write lock.          [KEPT — 0 violations]
  Coordination by shared-state reads,   [KEPT — 0 messages]
    never point-to-point messages.

EMERGENCE
  Gap-score every task.                 [KEPT]
  Auto-add high-confidence inferences,
    including routine caps like edge_cases. [FIXED calibration]
  Surface only genuinely uncertain items to operator.
  End-of-day learning to remove recurring defect classes. [KEPT]
  NO pre-emptive capability injection.  [CUT]

ROUTING
  Basic cognitive-load split: mechanical -> local, reasoning -> cloud. [KEPT]
  NO strict/forced routing beyond that. [CUT]

VALIDATION
  Validator checks every output.        [KEPT]
  Halt on FIRST raised signal.          [THRESHOLD CUT]
  Jidoka loop on halt: stop -> fix -> root-cause. [KEPT]
  NO peer-review pass.                  [CUT]

OBSERVABILITY
  Structured event log, trace ID per task. [KEPT]
```

**Robustness (final config, 8 seeds each):**

| Scenario | Cost/task | Defects shipped | Catch rate |
|---|---|---|---|
| Normal (5 days × 20) | 6.64 | 0.0 | 100% |
| 2× load (5 × 40) | 6.61 | 0.0 | 100% |
| Degraded agents | 7.70 | 0.0 | 100% |
| 2× load + degraded | 7.69 | 0.0 | 100% |

The tuned machine is not just cheaper — it is **load-stable and skill-robust**. Doubling throughput barely moves cost per task; halving agent skill raises it modestly while still catching everything.

---

## What This Says About the Design Series

The simulation vindicated the **structural** parts of the design (single entry point, atomic state, shared-state coordination, halt authority, observability — all kept and all working) while pruning the **elaborations** (threshold gating, strict routing, pre-emptive inference, peer review — all cut). 

The pattern is worth internalizing: the design docs' *architecture* was sound; several of their *added cleverness* mechanisms were not. The biological/organizational analogies that justified those elaborations (quorum thresholds, defense-in-depth review) are real in their home domains but did not transfer — precisely the risk the Lessons-Learned document warned about. The simulation was the tool that told the difference, which no amount of further reading would have.

**The honest caveat:** these results are only as good as the simulation's assumptions — the cost model (shipped defect = 8, false halt = 1.5), the agent skill levels, and the defect model are stylized. The *directions* are robust across seeds and stress tests, but before committing code, the highest-value move is to instrument the real repo to measure the two parameters that drove everything: **the real cost ratio of a shipped defect vs. a false halt**, and **the real defect rate of local vs. cloud agents.** If your true cost ratio is very different (e.g., false halts are catastrophic, not cheap), the threshold decision could flip — so measure it rather than trusting the sim's 8:1.

---

## The Harness

The four-version simulation (`map_v1.py`–`map_v4.py`) is a working, seeded, instrumented testbed. It's the artifact to keep: any future MAP change can be A/B tested in it before touching the real system. The next step, when ready, is to swap the stub agents for thin wrappers around the real `map-git`, `validate_task_graph.py`, and agent processes — one at a time — so the harness measures the real system instead of a model of it.

---

*Companion to the MAP series. Reports empirical results from the simulation harness against the design in MAP-Implementation-Roadmap.md and the two principles in 00-MAP-Index.md — including where the data overruled the design.*
