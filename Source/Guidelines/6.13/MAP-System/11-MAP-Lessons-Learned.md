# MAP: Documented Failures and Lessons Learned
### What Went Wrong in Each Research Area, and the Corresponding Caution for MAP

Every field discussed in the prior research document has real, documented failure modes — not just success stories. This matters because adopting a concept without its known failure modes means re-discovering them the hard way. Each section below: what failed, why, and the specific caution for MAP.

---

## 1. CRDTs — The Consistency-Is-Not-Correctness Problem

### What Failed / Was Learned
PayPal's own production CRDT deployment (Dmitry Martyanov, QCon/InfoQ, "CRDTs in Production") surfaced a critical distinction: **CRDTs guarantee convergence, not correctness.** A system can report "we are fine" — meaning all replicas agree — while the agreed-upon value is still wrong for the business logic at that moment in time. Convergence is a *consistency* guarantee, not a *correctness* guarantee, and conflating the two is the single most common production mistake.

Additional documented limitations:
- **No flow control.** Traditional systems can reject a conflicting write outright ("this operation cannot be executed"). CRDTs have no equivalent mechanism — every write is accepted and merged, even ones you might have wanted to block.
- **Storage and communication overhead.** Tracking causality metadata (needed to merge correctly) grows over time, especially for structures like sets that support removal — deleted elements often can't be fully purged without risking data corruption, so structures silently bloat.
- **Unique replica ID requirement.** Nearly all CRDT implementations require every node to have a globally unique ID; if two nodes accidentally share an ID, the result is silent data corruption, not a visible error.
- **Byzantine failure gap.** Standard CRDTs assume nodes are honest but possibly offline — they don't tolerate nodes that produce *actively wrong* data. A 2024/2025 VLDB paper ("Making CRDTs Not So Eventual") notes that naively bolting on Byzantine fault tolerance defeats the whole point of using CRDTs for performance.
- **Directly relevant finding**: a 2025 paper explicitly identifies that prior CRDT research targets *human-human* collaborative editing (Google Docs-style), and that applying strong eventual consistency to *autonomous LLM agent coordination* is an open research gap requiring new protocols and characterization of agent-specific failure modes — meaning if MAP adopts CRDTs, you would be working close to the frontier, not applying a fully solved recipe.

### Caution for MAP
If MAP adopts CRDT-style state (Section 1 of the prior document), do not treat "the repo converged" as "the repo is correct." A race condition producing an agreed-upon but wrong task ID would pass a naive convergence check. You would still need a separate correctness validator (which you're already planning) layered on top of, not instead of, convergence. Also: assign replica/agent IDs deliberately and centrally — an accidental ID collision under CRDTs corrupts data silently, which is a worse failure mode than your current visible repo-drift symptom.

---

## 2. Artificial Immune Systems — The False Positive Ceiling

### What Failed / Was Learned
This is the most heavily documented failure mode in the entire set of concepts discussed. Multiple independent sources converge on the same finding:
- The foundational critique (Stibor, 2006, theoretical; Kim, 2001, experimental) showed that simple negative-selection algorithms **scale poorly and produce low detection rates with excessive false positive rates** — proven both mathematically and empirically, not just anecdotally.
- Static detector strategies (fixed "radius" of what counts as similar-to-self) cause a direct tradeoff failure: too tight a radius causes false negatives (anomalies slip through), too loose causes false positives (legitimate behavior gets flagged as an intrusion) — and traditional AIS implementations struggle to tune this correctly without extensive prior knowledge of what "self" looks like.
- A Purdue dissertation on AIS-based intrusion detection identifies **higher computational overhead, higher false positive rates, and lower detection rates** as the specific reasons anomaly-based detection is *less* widely deployed than simpler signature-based detection, despite AIS's theoretical advantage of catching novel/unknown attacks.
- A broader review of anomaly detection systems notes a structural problem beyond AIS specifically: building "a solid model of what acceptable behavior is" is genuinely hard, and *normal behavior itself changes over time*, meaning the system requires continuous retraining or it drifts into producing more false alarms as legitimate usage patterns evolve.

### Caution for MAP
If you build the compliance validator around a "what does legitimate MATOCP output look like" pattern-matching approach (the AIS-inspired idea from the prior document), budget explicitly for a false-positive problem, not just a "does it catch violations" problem. A validator that's too strict will flag legitimate agent variation as non-compliant and erode your own trust in it (you'll start ignoring its alerts — the exact failure that made you need it in the first place). A validator that's too loose won't catch real drift. This is a real, unsolved tuning problem in the underlying research, not a solved one — expect to iterate on detector sensitivity the way the AIS literature has been iterating on it for 20+ years. Concretely: log false-positive rate as a tracked metric from day one, the same way the compliance telemetry section of your outline already proposes tracking violation frequency.

---

## 3. Braess's Paradox — The Intervention-Backfire Problem

### What Failed / Was Learned
The core "failure" here isn't a failure of the theory — Braess's Paradox is rigorously proven — it's a documented pattern of **well-intentioned infrastructure additions making things worse**, discovered repeatedly across independent domains:
- Roughgarden's 2006 result proved the effect **"can be arbitrarily severe in large networks"** — meaning the more complex a system gets, the worse an ill-considered addition can backfire, not better.
- The paradox has independently reappeared in domains far from traffic: electrical microgrids (adding a transmission line can increase congestion via Kirchhoff's laws) and social/recommendation networks (adding more product/content options can make outcomes worse for everyone) — suggesting this isn't a traffic-specific quirk but a general property of networks where independent agents make locally rational choices.
- The practical lesson documented across transportation case studies (Seoul, Stuttgart, NYC, London) is counter to instinct: **removing capacity sometimes helps**, and this is only knowable by measuring actual system behavior, not by reasoning about it in advance — planners who added capacity assuming it would help were repeatedly wrong until they started measuring.

### Caution for MAP
The lesson isn't "don't add infrastructure" — it's "don't assume infrastructure additions help without measuring, and expect the risk to grow as MAP gets more complex, not shrink." Every new hcom message type, every new validator, every new agent added to MAP is a candidate for this failure mode. Before adding a new coordination mechanism, the correct move (per this research) is to measure total system throughput/friction before and after — the same instinct that led traffic planners to discover that closing certain roads improved flow. This directly reinforces Tier-based rollout in your roadmap: add one piece, measure, then add the next, rather than building out the full compliance/routing/observability stack at once and assuming each piece is net-positive.

---

## 4. Traffic/Rail Control Metaphors — The Verification Gap

### What Failed / Was Learned
This one is a caution about the research itself, not about the underlying engineering: the specific translation of ramp metering, block signaling, and interlocking into distributed-computing research was not found as a dedicated, peer-reviewed literature in the searches performed. The actual computer-science equivalents (admission control, mutual exclusion, deadlock prevention) are well-established, but the traffic engineering versions and the CS versions were developed largely independently, not as a documented cross-pollination.

### Caution for MAP
Don't cite "ramp metering" or "block signaling" as if they were peer-reviewed computer science — they're useful design intuition, not validated research. If you build an admission-control mechanism for MAP's task queue, look up admission control and mutual exclusion literature directly rather than assuming traffic engineering research transfers cleanly. This is a caution about epistemic hygiene as much as about MAP's architecture: it's easy to let a good metaphor feel like it comes with more evidentiary weight than it actually has.

---

## Summary Table

| Concept | Core Documented Failure | Direct Caution for MAP |
|---|---|---|
| CRDTs | Convergence ≠ correctness; silent corruption on ID collision; no flow control | Keep a correctness validator on top of any CRDT layer; assign replica IDs deliberately |
| Artificial Immune Systems | High false-positive rates; requires continuous retraining as "normal" drifts | Track false-positive rate on the compliance validator from day one; expect to iteratively tune, not deploy once |
| Braess's Paradox | Interventions can make large, complex systems worse, more severely as they grow | Measure before/after when adding any new MAP infrastructure; roll out one Tier at a time |
| Traffic/rail control analogies | Not yet a validated CS research literature | Cite "admission control" / "mutual exclusion" directly, not the traffic metaphor |

---

*Companion document to MAP-System-Requirements-Outline.md, MAP-Philosophical-Foundations.md, MAP-Thesis.md, and MAP-Cross-Domain-Research.md*
