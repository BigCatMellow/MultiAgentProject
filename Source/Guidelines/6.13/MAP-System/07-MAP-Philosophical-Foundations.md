# Philosophical & Theoretical Foundations for MAP
### Thinkers, Concepts, and Primary Works Relevant to Multi-Agent System Design

---

## 1. Norbert Wiener — Cybernetics
**Core concept**: Systems that regulate themselves via feedback loops — correcting behavior based on the gap between intended and actual state.

**Applies to**: Event validator, andon-style halting, compliance telemetry. These are all cybernetic feedback loops in Wiener's original sense — MAP is a control system, not just software.

**Primary works**:
- *Cybernetics: Or Control and Communication in the Animal and the Machine* (1948)
- *The Human Use of Human Beings* (1950) — more accessible entry point

---

## 2. Stafford Beer — Viable System Model (VSM)
**Core concept**: A framework for organizations made of semi-autonomous subunits that each need independence to function while still cohering into one viable whole. Five explicit subsystems: implementation, coordination, control, intelligence, policy.

**Applies to**: The HPOM / hcom / emergence relationship. This is the single most directly applicable framework in this list — a near-existing architecture for recursive, autonomous subsystems, which is MAP's exact shape.

**Primary works**:
- *Brain of the Firm* (1972) — introduces the Viable System Model
- *The Heart of Enterprise* (1979) — deeper technical treatment of VSM
- *Diagnosing the System for Organizations* (1985) — practical/applied version, likely the most directly usable

**Recommendation**: read this one first if only reading one.

---

## 3. W. Ross Ashby — Law of Requisite Variety
**Core concept**: A controlling system must have at least as much internal complexity ("variety") as the system it is trying to control, or it cannot regulate it.

**Applies to**: Whether HPOM, as currently built, is even structurally capable of controlling the combined behavior of all agents it dispatches to — a concrete test for orchestrator adequacy, independent of protocol quality.

**Primary works**:
- *An Introduction to Cybernetics* (1956) — contains the Law of Requisite Variety
- *Design for a Brain* (1952) — earlier, more foundational

---

## 4. Friedrich Hayek — The Knowledge Problem
**Core concept**: No central planner can hold all the locally-distributed knowledge scattered across a system; this is the argument for decentralized coordination over central planning.

**Applies to**: The philosophical case *for* a federated architecture (multiple canonical repos with sync contracts) over a single central orchestrator — pulls in the opposite direction from Ashby's Requisite Variety, and both are legitimate positions to weigh against each other.

**Primary works**:
- "The Use of Knowledge in Society" (1945) — essay, *American Economic Review* — the essential text
- *The Road to Serfdom* (1944) — broader context, less directly applicable

---

## 5. Ludwig Wittgenstein — Rule-Following Paradox
**Core concept**: No rule can fully specify its own correct application in every case — there is always a gap between a written rule and what counts as "following" it.

**Applies to**: The philosophical root of the compliance-drift problem. MATOCP isn't necessarily badly written — *any* written protocol has this gap. This is the argument for why a separate verification layer, not a better-written rule, is the correct structural fix.

**Primary works**:
- *Philosophical Investigations* (1953) — see especially §§185–242, the "rule-following considerations"
- Saul Kripke's *Wittgenstein on Rules and Private Language* (1982) — the influential secondary reading that made this argument famous; often more approachable than the original

---

## 6. Michael Polanyi — Tacit Knowledge
**Core concept**: "We know more than we can tell" — some competent behavior cannot be fully reduced to explicit, statable rules.

**Applies to**: Why some agent judgment calls will always need escalation paths and human review rather than exhaustive protocol coverage. There is a ceiling on how much of "doing this well" can ever be written down as a spec.

**Primary works**:
- *Personal Knowledge: Towards a Post-Critical Philosophy* (1958)
- *The Tacit Dimension* (1966) — shorter, the more commonly cited entry point

---

## Summary Table

| Thinker | Concept | MAP Application | Best Starting Text |
|---|---|---|---|
| Norbert Wiener | Cybernetics / feedback loops | Event validator, self-correction | *The Human Use of Human Beings* |
| Stafford Beer | Viable System Model | HPOM/hcom/emergence architecture | *Diagnosing the System for Organizations* |
| W. Ross Ashby | Law of Requisite Variity | Is HPOM complex enough to control its agents? | *An Introduction to Cybernetics* |
| Friedrich Hayek | Knowledge problem | Case for federated vs. central architecture | "The Use of Knowledge in Society" (essay) |
| Ludwig Wittgenstein | Rule-following paradox | Why protocols alone can't ensure compliance | Kripke's *Wittgenstein on Rules and Private Language* |
| Michael Polanyi | Tacit knowledge | Why escalation paths are necessary, not optional | *The Tacit Dimension* |

---

## Reading Priority (if approached sequentially)

1. **Stafford Beer**, *Diagnosing the System for Organizations* — most directly usable, closest to an off-the-shelf architecture
2. **Ludwig Wittgenstein** (via Kripke's secondary text) — explains *why* the compliance layer is structurally necessary, not just a nice-to-have
3. **W. Ross Ashby**, *An Introduction to Cybernetics* — short, gives a concrete test for orchestrator adequacy
4. **Friedrich Hayek**, "The Use of Knowledge in Society" — single essay, informs the federated-vs-central architecture decision
5. Wiener and Polanyi — useful framing, lower urgency; read opportunistically

---

*Companion document to MAP-System-Requirements-Outline.md*
