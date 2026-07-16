# MAP Simulation Results, Round 4: Chaos Engineering
### A Different Test Entirely — Inject Faults, Measure Survival

The first three rounds optimized cost. This one changes methodology: it **injects faults** — crashes agents mid-task, drops writes, corrupts shared state — and measures whether MAP recovers or cascades. It tests the resilience layer (idempotency keys, dead-letter queue, circuit breakers, blast-radius containment) that the synthesized doc asserts but had never validated. And it runs the Braess check on each mechanism: remove it and see if survival craters.

Results from `chaos.py` and `breaker_fair.py`, 8 seeds each, under a heavy baseline fault load (10% crash, 8% timeout, 6% corrupt-write per attempt).

---

## Finding 1: Resilience as a category is unambiguously essential

- **Full stack under heavy fault load: 100% task success, 0 lost, 0 cascaded.**
- **No resilience at all: 38.7% success, 62 tasks lost, 244 cascade failures.**

A system with none of the resilience layer collapses under crashes and corruption. This is not a marginal optimization — it's the difference between a system that survives failure and one that dies from it.

---

## Finding 2 (the Braess check): All four mechanisms earn their place — each under a distinct failure mode

Removing each mechanism one at a time from the full stack:

| Removed | Success | Lost | Cascaded | Double-applies | Verdict |
|---|---|---|---|---|---|
| (nothing) | 100% | 0 | 0 | 0 | — |
| Blast-radius | **44%** | 0 | **280** | 0 | **Most load-bearing** |
| Dead-letter | **76%** | **122** | 0 | 0 | **Severe if removed** |
| Idempotency | 100% | 0 | 0 | **33** | **Subtle but real** |
| Circuit breaker | 100% | 0 | 0 | 0 | Needed a fair test (see Finding 3) |

- **Blast-radius containment is the single most important:** without it, one uncontained corrupt write poisons everything downstream that reads shared state — 280 cascade failures, success down to 44%. This is the mechanism that stops one bad write from taking down the system.
- **Dead-letter queue is severe if removed:** without a retry queue, every crashed or timed-out task is simply lost — 122 gone. It's what makes failure recoverable rather than terminal.
- **Idempotency is the dangerous-to-miss one:** removing it doesn't change success rate at all, but produces **33 silent double-applied writes** — a *correctness* corruption invisible to the obvious metric. If you only watched success rate, you'd wrongly conclude idempotency does nothing. It earns its place for a reason you have to look for.

---

## Finding 3: The circuit breaker — a lesson in testing mechanisms under the right conditions

The chaos test initially made the circuit breaker look useless: removing it changed nothing (100% success either way). By the round's own Braess logic, that flagged it for cutting.

**But that test was unfair, and being skeptical of the result was correct.** The breaker's purpose is not uniform random failure — it exists for *one persistently broken agent* (a bad deploy, a wedged local model, a sick node). The chaos test applied failures uniformly across all agents, which is not the breaker's job. Re-tested under its actual purpose — one agent failing 85% of its tasks:

- **With breaker: 4 tasks routed to the sick agent before it's pulled from rotation, 526 total work attempts.**
- **Without breaker: 159 tasks routed to the sick agent, 654 total work attempts.**

The breaker avoids 128 wasted attempts, and the gap *widens* as the agent gets sicker (585 → 688 work as failure climbs to 99%). **It earns its place — but only visibly when tested against the failure mode it was designed for.**

This is the same lesson as Round 2's GIL thread-race: **test a mechanism under the condition it actually exists for, or the test lies about it.** A resilience mechanism aimed at persistent failure will look worthless under random failure, and vice versa.

---

## Finding 4: The full stack degrades gracefully, not catastrophically

Cranking the fault load up:

| Fault load | Success | Lost | Cascaded |
|---|---|---|---|
| Baseline | 100% | 0 | 0 |
| 2× | 99% | 5 | 0 |
| 3× | 86% | 69 | 0 |

Even at triple the fault rate, the system degrades smoothly (100% → 99% → 86%) rather than hitting a cliff, and — importantly — **cascades stay at zero throughout**, because blast-radius containment holds. Graceful degradation under rising stress is the signature of a resilient system.

---

## What This Round Confirms for the Synthesized Doc

The resilience layer is **validated in full** — all four mechanisms earn their place, each defending against a distinct failure mode:
- **Blast-radius** → stops corrupt state from cascading (the most critical)
- **Dead-letter** → makes crashed/timed-out tasks recoverable rather than lost
- **Idempotency** → prevents silent double-applies (a correctness bug, not a throughput one)
- **Circuit breaker** → contains a persistently broken agent (visible only under that scenario)

No changes to the doc's resilience layer are needed — but this round adds the specific evidence and the failure mode each mechanism owns, which the doc previously asserted without proof.

---

## The Standing Pattern Across Four Rounds

- **Round 1** cut four mechanisms that made MAP worse (threshold gating, strict routing, pre-tokenization, peer review).
- **Round 2** corrected the concurrency requirement (cross-process, not thread) and resolved the threshold question via accuracy.
- **Round 3** kept the knowledge layer but proved it only works in full, and named its payoff conditions.
- **Round 4** validated the resilience layer in full — and re-confirmed the meta-lesson that a mechanism must be tested under the failure mode it's designed for, or the test misleads.

Four rounds, four different methodologies (cost sweep, break-even + real concurrency, knowledge-layer economics, fault injection). The discipline held throughout: stay committed to nothing the data doesn't support — which sometimes means cutting, sometimes correcting, sometimes validating while sharpening, and sometimes distrusting your own first result until you've tested it fairly.

---

*Round-4 companion to the earlier simulation results. Harness: chaos.py, breaker_fair.py.*
