# MAP Simulation Results, Round 3: The Knowledge Layer
### Testing the Newest, Least-Proven Component — Does the Library Agent Earn Its Place?

The Library/knowledge layer (component 9) was added on reasoning alone, after the earlier simulation rounds. This round tests it directly, under the same discipline: prove it pays off or cut it. The result is that it earns its place decisively — but the simulation also proves that *how* it's built matters enormously, and that a partial implementation is worse than nothing.

Results from `knowledge_layer.py` and `knowledge_stress.py`, 6 seeds each.

---

## The Test

Four configurations, cost measured in tokens (defects converted to token-equivalent, since a bad decision from stale/lossy context is caught late and expensive):

- **NO_LIBRARY** — agents always read full docs. Expensive, but always current and complete.
- **SUMMARY_ONLY** — agents read summaries. Cheap reads, but risk acting on a stale summary or missing needed detail.
- **SUMMARY_LINKS** — summaries plus wikilinks; agents traverse to full detail when a task needs it. Kills lossiness; staleness remains.
- **SUMMARY_LINKS_TRACK** — adds event-driven staleness tracking (a changed doc's summary is regenerated before it's read again). The full synthesized-doc design.

Swept across churn rate (how often docs change) and detail-need rate (how often a task needs full detail, not just the summary).

---

## Finding 1: The full design wins everywhere — 34% to 85% cheaper than no library

SUMMARY_LINKS_TRACK was cheapest in every one of nine regimes tested, from 34% cheaper than no-library (high churn, high detail-need) to 85% cheaper (low churn, low detail-need). The Library agent is validated.

---

## Finding 2 (the real lesson): A partial build is a net loss

This is where the simulation earned its keep. The intermediate configurations are traps:

- **SUMMARY_ONLY is worse than having no library at all — in every regime.** It cost 4.8M–17.8M tokens versus 4M for no library, because stale and lossy defects cost far more than the cheap reads save. A library that only summarizes — without wikilinks to detail and without staleness tracking — is *actively harmful*.
- **SUMMARY_LINKS (wikilinks but no staleness tracking) is only sometimes better than no library.** It wins at low churn but at 30% churn it costs 7.8M–10.9M — near or worse than no-library — because staleness defects accumulate.

The implication: this component cannot be built halfway. Shipping summaries without the full apparatus would have made MAP measurably worse, which is exactly the outcome the "prove it earns its place" discipline exists to catch.

---

## Finding 3: Staleness tracking is the load-bearing feature

The value of the Library agent is **not** the summarization. It is the **event-driven staleness invalidation.** That single feature is what separates the 80%-cost-cut configuration from the net-loss configurations, and its importance *grows* with file churn. The synthesized doc has been corrected to reflect this: staleness tracking is not one of two optional failure-mode mitigations — it is the non-negotiable core that makes the component viable.

---

## Finding 4: The conditions where it would stop being worth it

The full-design win looked almost too clean, so the stress test pushed the assumptions until the recommendation flips — to make the advice conditional and honest:

- **Regeneration cost:** tracking wins until re-summarizing a doc costs ~16,000 tokens — 8× the cost of reading the full doc. That's implausible (summarizing is cheaper than reading, not 8× more expensive), so this never flips in practice. **Robust.**
- **Compression ratio:** tracking wins until compression drops below ~1.2×. This is the meaningful boundary — **if summaries aren't at least ~1.5× smaller than their source, the layer isn't worth it.** In practice summaries run 5–20× smaller, comfortably clear, but it names the condition to watch: if a "summary" ever approaches the size of the original, that file shouldn't be in the summarized set.
- **Which model regenerates:** cheap-tier regeneration costs ~57% less than reasoning-tier for the same work. This empirically confirms the roster placement — summary maintenance belongs on the cheap-language tier, never on an expensive reasoning agent.

---

## What Changed in the Synthesized Doc

Two corrections, both from this round:
1. **Staleness tracking elevated from "one of two mitigations" to "the load-bearing core"** — with the explicit finding that a summaries-only library is worse than no library.
2. **Two payoff conditions added** — real compression (≥ ~1.5×) and cheap-tier regeneration — as things to watch, outside which the component should be reconsidered.

The component survives, but the simulation made its design requirements precise rather than aspirational — and confirmed that building it partially would have been a mistake.

---

## The Standing Pattern Across All Three Rounds

Round 1 cut four mechanisms that made MAP worse. Round 2 corrected the concurrency requirement and resolved the threshold question via accuracy. Round 3 kept a component but proved it only works in full and named the conditions on it. The through-line: **measurement keeps the system honest** — sometimes it cuts a beloved mechanism, sometimes it corrects a requirement, sometimes it validates an addition while sharpening exactly how it must be built. The discipline is the same in all three: stay committed to nothing that the data doesn't support.

---

*Round-3 companion to MAP-Simulation-Results.md and MAP-Simulation-Results-Round2.md. Harness: knowledge_layer.py, knowledge_stress.py.*
