# MAP Simulation Results, Round 5: Emergence Learning Dynamics
### A Longitudinal Test — Does the Self-Improvement Loop Converge, or Degrade?

Every prior round was static — a snapshot under fixed conditions. This one is a **dynamics test**: run emergence's end-of-day learning loop over a long horizon (40 days) and watch the trajectory. A self-improvement loop that adds heuristics from recurring misses has three real failure modes: it could never converge, it could over-learn (add capabilities that cost more than they save — the pre-tokenization failure, self-inflicted), or it could learn noise. This round tests which happens, and adds a missing piece to the synthesized system.

Results from `emergence_dynamics.py` and `emergence_dynamics2.py`, 6–8 seeds each.

---

## Finding 1: The loop converges — fast and cleanly

The good news first: end-of-day learning drives defects from **28 on day 0 to 0 by day 5**, cutting total cost from 223 to ~83 (a 63% reduction) and then holding steady. It does not oscillate, does not diverge, and reaches a stable state quickly. The self-improvement loop works.

---

## Finding 2 (a flaw in the first test, reported honestly)

The first version of the test produced **zero spurious heuristics in every configuration** — which meant it couldn't evaluate the guard it was built to test, because the failure mode never occurred. The reason was a modeling flaw: the test only let emergence learn capabilities that were *genuinely needed*, so every heuristic it learned was correct by construction. Real learning works from *observed misses*, which include noise and **misattribution** — a defect blamed on the wrong cause.

This is the same discipline as Round 2 (the GIL thread-race) and Round 4 (the circuit breaker): **a test that can't produce the failure it's checking for tells you nothing.** The model was fixed to inject misattribution — a defect sometimes blamed on a random capability rather than its true cause — so spurious heuristics can actually form. Only then could the guard be evaluated.

---

## Finding 3: Without a guard, the loop over-learns — and it gets worse with noise

With realistic misattribution (25%), the trajectories diverge:

| | Unguarded | Guarded (prunes useless heuristics) |
|---|---|---|
| Steady-state cost | 93.7 | 85.6 |
| Spurious heuristics | 1.2 (permanent) | 0.0 |
| Defects | 0.0 | 0.5 |

The unguarded loop accumulates **permanent spurious heuristics** — learned from misattributed defects, they fire on every matching task forever, adding work with no benefit. The guarded loop (which prunes any heuristic that fires repeatedly but never actually prevents a defect) keeps spurious heuristics at zero.

The sensitivity sweep is the decisive part — **the guard's value grows sharply with noise:**

| Misattribution rate | Unguarded cost | Guarded cost | Unguarded spurious heuristics |
|---|---|---|---|
| 10% | 85.2 | 91.1 | 0.2 |
| 25% | 93.7 | 85.6 | 1.2 |
| 40% | 108.5 | 89.8 | 3.1 |
| 60% | 153.6 | 87.1 | 8.4 |

Unguarded cost climbs from 85 to 154 as misattribution rises; guarded stays pinned near 87. Notably, at very low noise (10%) the guard slightly *costs* more — the pruning overhead isn't worth it when there's nothing to prune. But at any realistic noise level, the guard becomes essential and the gap widens fast.

---

## Finding 4: This is the pre-tokenization failure, arising from the loop's own dynamics

Round 1 cut "pre-defining tokenization" because it added capabilities (and work) for defects the validator already caught — a net-negative elaboration. This round shows the *same failure can emerge from within* emergence's learning loop: an unguarded loop teaches itself to over-include capabilities, recreating exactly the over-elaboration that was manually cut. The self-improvement mechanism, left unbounded, re-introduces the very failure the system was tuned to remove. That makes the pruning guard not optional polish but a necessary counterweight to the loop's natural tendency.

---

## What Changed in the Synthesized Doc

The emergence component previously described end-of-day learning but **never specified a bound on it** — a real gap. Added:
- **A pruning guard is now part of the design:** any learned heuristic that fires repeatedly but never actually prevents a defect must be pruned. Unbounded learning is explicitly flagged as unsafe — it is the pre-tokenization over-learning failure arising endogenously.
- **The noise-dependence is noted:** the guard is slightly wasteful at very low noise and essential at realistic noise, so it should be on by default.

---

## The Standing Pattern Across Five Rounds

- **Round 1** cut four net-negative mechanisms.
- **Round 2** corrected the concurrency requirement (cross-process) and resolved the threshold question via accuracy.
- **Round 3** kept the knowledge layer but proved it only works in full, with named conditions.
- **Round 4** validated the resilience layer in full, each mechanism owning a failure mode.
- **Round 5** validated the learning loop's convergence but found it needs a pruning guard against endogenous over-learning.

Five rounds, five methodologies (cost sweep, break-even + concurrency, knowledge economics, fault injection, longitudinal dynamics). And a recurring meta-lesson now seen three times: **a test that cannot produce the failure it's checking for must be fixed before it's trusted** — the GIL race, the circuit breaker, and now the spurious-heuristic guard were all initially masked by a test that couldn't generate the relevant failure. The discipline holds: commit to nothing the data supports, and distrust data from a test that can't fail.

---

*Round-5 companion to the earlier simulation results. Harness: emergence_dynamics.py, emergence_dynamics2.py.*
