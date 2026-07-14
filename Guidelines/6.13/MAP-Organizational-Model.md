# MAP Organizational Model: A Cherry-Picked Hybrid
### The Best Elements From Multiple Business/Structure Models, Mapped to MAP

This document does in-depth work on the organizational-model side. Rather than adopting one management system wholesale, it deliberately cherry-picks the highest-value mechanisms from several — and pairs each with the specific MAP subsystem it improves. The premise (established earlier and reinforced by the research below): **no single organizational model should be applied uniformly**, because each was built for a different problem and each has a documented failure mode when copied blindly.

The most important finding across all the research: **every one of these models fails the same way when adopted as a label instead of a mechanism.** The Spotify literature is unanimous on this — copying the structure without the culture "produces the same dysfunction with new labels." So this document extracts *mechanisms* (things that do work), not vocabulary.

---

## Model 1: Toyota Production System (Lean) — For the Execution Layer (HPOM)

TPS is built on two pillars: Just-in-Time and **Jidoka**. Jidoka is the one worth taking whole, and it's more precisely defined than the earlier discussion captured.

### Cherry-pick: Jidoka's four-step loop
Jidoka ("autonomation" — automation with human intelligence) is a complete, ordered procedure, not just "stop on error":
1. **Detect the abnormality** — a machine or worker notices a deviation.
2. **Stop** — halt immediately to prevent producing more defective items.
3. **Fix the immediate problem** — restore flow.
4. **Investigate and solve the root cause** — change the process so it can't recur (often via 5 Whys).

The origin story is instructive: it began in 1896 with Sakichi Toyoda's automatic loom that stopped the instant a thread broke, so it never wove flawed cloth. That is exactly the behavior MAP's event validator should have.

**For MAP (HPOM/event validator)**: the validator shouldn't just log and alert — it should have the *authority to halt* (step 2), and every halt should trigger a mandatory root-cause step (step 4) that updates the process, not just patches the instance. This is the difference between MAP catching the same failure repeatedly and MAP becoming immune to it. Note the explicit distinction the research draws: **Jidoka detects and responds in real time; Poka-Yoke prevents the error from being possible at all.** You want both — Jidoka for the event validator, Poka-Yoke (structural impossibility, per the formal-verification doc) for the P0 invariants.

### Documented limit
Jidoka demands investment in detection and a genuine culture of stopping. A halt authority nobody trusts (or that fires constantly on false positives) gets ignored — which loops directly back to the false-positive ceiling from the Lessons-Learned doc. The halt must be well-calibrated or it becomes noise.

---

## Model 2: Team Topologies — For the Whole-System Structure

This is the most rigorous of the frameworks and the best-suited to MAP overall, because its organizing principle is **cognitive load** — and that maps almost perfectly onto agent context limits. One 2026 source is already applying it to AI agent harnesses explicitly. It defines exactly four team types and three interaction modes.

### Cherry-pick 1: The four team types as MAP subsystem roles
- **Stream-aligned team** (the default; most teams should be this): owns one valuable flow end-to-end. → In MAP, the **agents actually executing a task** are stream-aligned — each owns a task from start to finish with minimal handoffs.
- **Platform team**: provides self-service capabilities that reduce others' cognitive load. → MAP's **shared canonical state, allocator, lock, and validators** are a platform — infrastructure the execution agents consume so they don't each reinvent coordination.
- **Enabling team**: temporarily helps others build a capability, then leaves. → MAP's **emergence subsystem** is enabling — it augments a task with inferred requirements, then steps back.
- **Complicated-subsystem team**: owns a piece of deep specialist complexity to spare everyone else the cognitive tax. → MAP's **formal-verification / TLA+ layer** (or any single genuinely hard component) is a complicated-subsystem — isolated so its complexity doesn't leak into every agent.

### Cherry-pick 2: Cognitive load as the sizing principle
The core insight: **a team's cognitive capacity is finite; when the domain it owns exceeds that capacity, delivery slows and quality drops.** The other three team types exist *only* to absorb load off the stream-aligned team. For MAP with local models especially, this is gold: an agent (particularly a small local one) has a hard cognitive-load ceiling, and the entire point of the platform/enabling/complicated-subsystem split is to keep each agent's load under that ceiling. This is the rigorous version of your local-model routing problem — route by cognitive load, not just task type.

### Cherry-pick 3: Team APIs and interaction modes
Every team exposes a **one-page "team API"** (its services, SLAs, docs, how to interact) and uses one of three interaction modes: **collaboration** (close, temporary, expensive — sustained collaboration signals unclear boundaries), **X-as-a-Service** (clean consumption, the mature default), and **facilitating** (coaching, then disengaging). 

**For MAP**: each subsystem should expose a defined interface (a "subsystem API"), and the target state is **X-as-a-Service** between them — the execution agents consume the allocator "as a service," not by collaborating with it every call. The research's warning is directly useful: **sustained collaboration between two teams means their boundary is wrong.** If two MAP subsystems are constantly chattering (lots of hcom traffic between them), that's a signal to redraw the boundary, not add more messaging.

### Why this one is the backbone
Martin Fowler's framing is the honest one: "all models are wrong, some are useful" — four team types can't capture every real org, but *the constraint is what makes it useful.* It forces evolution toward flow. And uniquely, its central metric (cognitive load) is the one that most directly translates from human teams to AI agents.

---

## Model 3: Spotify Model — For Extracting Two Specific Mechanisms Only

The Spotify model is the most-copied and most-misunderstood org model of the last decade — and even Spotify has publicly abandoned it. The research is emphatic that it was **a snapshot, not a framework**, and that it was "20 percent structure and 80 percent culture." So this section takes only the two mechanisms that survive scrutiny and discards the rest.

### Cherry-pick 1: The alignment-vs-autonomy matrix
The single most durable idea from Spotify. The goal is neither pure autonomy (→ chaos) nor pure alignment (→ conformism), but **both at once**: units that know *where* the system is going (alignment) and freely decide *how* to get there (autonomy). The diagnostic question is universal: "Do our units know where we're heading, and do they have the freedom to decide how they get there?"

**For MAP**: agents should receive a clear *what/why* (the mission and the canonical goal — alignment) but retain freedom over *how* they execute (autonomy). Over-specifying the "how" kills the benefit of using capable agents; under-specifying the "what" causes the drift you've already seen. This matrix is the tuning dial.

### Cherry-pick 2: Decoupled releases / limited blast radius
Spotify changed its architecture so squads owned specific slices, making **decoupled releases with a "limited blast radius"** — if one deployment fails, the failure is contained to its immediate area rather than taking down the whole product.

**For MAP**: this is the error-containment / circuit-breaker principle (from the requirements outline) expressed architecturally. Partition MAP so that one agent's failure has a limited blast radius — it corrupts its own task's state, not the canonical whole. This also echoes the subway "block" and coagulation "spatial containment" ideas from the cross-domain research.

### What to explicitly discard
The vocabulary (squads/tribes/chapters/guilds), the rigid structure, and any notion that adopting the labels produces the results. The research documents that autonomy without an alignment-and-guidance process "led to a lot of wasted time and unshared knowledge," and that it only worked because Spotify invested heavily in internal tooling and CI/CD — without that technical foundation, "squad autonomy is theoretical." For MAP, the parallel: agent autonomy is theoretical without the platform layer (Model 2) underneath it.

---

## Model 4: German Mittelstand / Six Sigma — For State Ownership

Retained from the earlier discussion, now sharpened. For the canonical-state and repo-ownership layer, the right culture is deliberately conservative: formal documentation, standardized procedure, quality gates before anything ships, zero improvisation. Six Sigma's contribution specifically is the **root-cause discipline** (5 Whys, Fishbone/Ishikawa) that pairs with Jidoka's step 4 — a structured method for the "investigate and solve the root cause" step rather than an ad-hoc guess.

**For MAP**: canonical state changes go through a formal gate with documentation, and every incident gets a structured root-cause analysis (5 Whys) rather than a quick patch. This is the least "agile" part of MAP on purpose — it's the part where improvisation caused the near-deletion incident.

---

## The Cherry-Picked Hybrid, By Subsystem

| MAP subsystem | Model borrowed from | Specific mechanism |
|---|---|---|
| HPOM / event validator (execution) | Toyota / Lean | Jidoka four-step loop: detect → stop (with authority) → fix → root-cause |
| Whole-system structure | Team Topologies | Four team types as subsystem roles; cognitive load as sizing/routing principle; X-as-a-Service interfaces |
| Agent task assignment | Spotify (matrix only) | Alignment on *what/why*, autonomy on *how* |
| Fault isolation | Spotify (blast radius only) | Decoupled execution; one agent's failure contained to its own task |
| Canonical state / repo ownership | Mittelstand + Six Sigma | Formal gates, documentation, 5 Whys root-cause discipline |
| P0 invariants | Toyota (Poka-Yoke) + formal methods | Structural impossibility of the error, proven (TLA+) |

---

## The Meta-Principle That Ties It Together

Across all four models, one principle recurs and is worth stating as MAP's organizational spine: **absorb cognitive load off the unit doing the valuable work, and give that unit alignment on the goal plus autonomy on the method.** Team Topologies states it most rigorously (load absorption), Spotify states the second half (alignment + autonomy), Lean provides the safety mechanism (Jidoka) that lets autonomy be safe, and Mittelstand provides the conservative anchor (formal state ownership) that keeps the autonomous parts from corrupting the shared foundation.

This is also why the cherry-pick works and wholesale adoption doesn't: these four are not competing systems to choose between — they're four different organs, each solving a different part of the same body's problem. MAP needs the heart, the immune system, the skeleton, and the nervous system; it does not need four hearts.

---

## Build Guidance

If acting on this, the order that respects dependencies:
1. **Team Topologies backbone first** — decide which subsystem is which of the four types, and define each one's "subsystem API." This clarifies everything else.
2. **Jidoka on the event validator** — give it halt authority and a mandatory root-cause step.
3. **Alignment/autonomy tuning** on task dispatch — clear what/why, free how.
4. **Blast-radius partitioning** — contain agent failures.
5. **Mittelstand gates** on canonical state — the conservative anchor, added deliberately.

---

*Companion document to the MAP series. Extends the organizational-analogues section (VIII) of MAP-System-Requirements-Outline.md with in-depth, cherry-picked mechanisms. Governed by the two design principles in MAP-Index.md.*
