# MAP Simulation Results, Round 6: Global Sensitivity Analysis
### Grading How Much to Trust Everything Else — and Where the Simulation Value Ends

This round doesn't test a new mechanism. It grades the reliability of the conclusions from all prior rounds by stress-testing each across the *full plausible range* of its underlying assumptions, then measuring the fraction of that range where the conclusion still holds. High fraction = robust, safe to build on. Low fraction = conditional, an outcome that depends on parameters we haven't measured on the real system.

This is the direct antidote to the gap register's "meta-hole" (the simulations share a mental model with the design). It's also, honestly, near the endpoint of what simulation can contribute — because its finding is that the remaining uncertainty lives in *unmeasured real-repo parameters*, not in anything more simulation can resolve.

Results from `sensitivity.py`.

---

## The Grades

| Conclusion | Holds across | Verdict |
|---|---|---|
| **C1 — Eager halt beats threshold gating** | **92%** of space | Mostly robust — trust it |
| **C2 — Knowledge layer (full) beats no-library** | **69%** of space | **Conditional — depends on your corpus** |
| **C3 — Idempotency prevents silent corruption** | **94%** of space | Mostly robust — trust it |
| **C4 — Emergence needs a pruning guard** | **75%** of space | **Conditional — depends on your noise level** |

---

## The Two Robust Conclusions (build on these)

**C1 — Eager halt beats threshold gating (92%).** The single biggest correction from the whole effort holds across nearly the entire plausible space of cost ratios, defect rates, and false-positive rates. The ~8% where it flips is the far corner where false positives are very frequent *and* shipped defects are cheap — two conditions that rarely coexist. This is safe to build on.

**C3 — Idempotency prevents silent corruption (94%).** Robust across crash frequencies and retry probabilities. The resilience layer's subtlest mechanism earns its place across essentially all realistic failure regimes.

---

## The Two Conditional Conclusions (measure before trusting)

These are the valuable findings, because the analysis pinpoints *exactly which real-repo measurements decide them* — turning vague uncertainty into a specific to-do list.

**C2 — The knowledge layer beats no-library only 69% of the space.** It flips in the low-compression / low-churn / low-detail-need corner: if your files don't compress much *and* rarely change *and* tasks rarely need full detail, the Library agent isn't worth its overhead. This confirms Round 3's payoff conditions were real, not hedging. **What to measure on the real repo:** the actual compression ratio of your docs (are summaries genuinely ~2×+ smaller?) and the real file churn rate. If both are low, reconsider the Library layer for that corpus.

**C4 — Emergence needs a pruning guard only 75% of the space.** At low misattribution (accurate inference), the guard's pruning overhead isn't worth it — consistent with Round 5's low-noise finding. The guard is correct *if* emergence's real-world inference is noisy enough to produce spurious heuristics; if inference is very accurate, the guard is roughly neutral. **What to measure:** emergence's real misattribution rate — how often a defect gets blamed on the wrong cause. Above ~20%, keep the guard; below, it's optional.

---

## What This Means for the Whole Body of Work

Two of the four headline conclusions are **regime-dependent, not universal.** This is not a failure of the earlier rounds — each held in the regimes it tested — but it corrects any impression that the findings are unconditional laws. The honest picture:

- The **structural** conclusions (eager halt, idempotency, and by extension the concurrency and coordination findings) are robust across wide assumptions.
- The **economic** conclusions (the knowledge layer, the learning guard) are conditional on parameters specific to how MAP is actually used — and those parameters have never been measured.

This maps precisely onto the gap register's #1 priority: **the remaining uncertainty is not resolvable by more simulation — it requires measuring real-repo parameters.** The sensitivity analysis is the proof of that claim: it shows the conditional conclusions flip based on exactly the numbers (compression, churn, misattribution) that only the real system can supply.

---

## The Honest Statement on Continued Simulation

Six rounds, six methodologies. The value has been real and specific: four mechanisms cut, two requirements corrected, two components validated-with-conditions, two black boxes partially specified, and now a reliability grade on all of it. But this round marks a genuine inflection: **further simulation of the same kind now has diminishing value**, because the analysis itself shows the open questions live in unmeasured real-world parameters, not in the model. More rounds would mostly re-confirm robust conclusions and re-flip conditional ones depending on which assumptions we chose — generating data without reducing the uncertainty that actually matters.

The genuinely high-value work from here is different in kind, and the gap register already ranks it: **measure the four driving parameters on the real repo** (which converts the two conditional conclusions into settled ones), **specify the decomposer** (the remaining black box), **design committed-state recovery**, and **write a threat model**. None of these are simulation. The simulation phase has largely delivered what it can — a well-stress-tested design and, crucially, a clear-eyed map of which of its conclusions to trust outright and which to verify against reality first.

---

## Standing Summary Across All Six Rounds

1. **R1** — cut four net-negative mechanisms.
2. **R2** — corrected concurrency (cross-process) and threshold (via accuracy).
3. **R3** — knowledge layer works, but only in full, with conditions.
4. **R4** — resilience layer validated, each mechanism owning a failure mode.
5. **R5** — learning loop converges but needs a pruning guard.
6. **R6** — graded all conclusions: two robust, two conditional-on-real-parameters — and identified that the remaining value is measurement, not simulation.

The discipline held to the end: commit to nothing the data doesn't support, distrust data from a test that can't fail, and — the final lesson — **know when the data has given what it can, and the next move belongs to the real system.**

---

*Round-6 capstone companion to the simulation-results series. Harness: sensitivity.py. This is the natural endpoint of the simulation phase; the register's real-repo actions are what follow.*
