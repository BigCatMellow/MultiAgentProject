# MAP Implementation Roadmap
### One Dependency-Ordered Build Plan Across the Whole Series

Each document in the MAP series carries its own local roadmap, and several of them reasonably claim to come "first." This document reconciles them into a single build order based on **actual dependencies** — what genuinely cannot be built until something else exists — rather than each subsystem's view of its own importance.

The plan is organized into seven phases. Each phase lists what it depends on, what to build, what "done" looks like, and which source documents it draws from. A phase should not start until its dependencies are met; within a phase, items can often proceed in parallel.

---

## The One-Sentence Logic of the Ordering

**You cannot enforce what you cannot route through one point; you cannot route safely through one point without knowing your state is correct; you cannot know your state is correct without being able to see it.** So the order is: correct state → single entry point → visibility → enforcement → intelligence → resilience → governance.

---

## Phase 0 — Foundations: Correct, Singular State
*Depends on: nothing. This is bedrock.*

Everything else reads and writes state, so state correctness comes before all of it. This is also where the incident that started everything gets closed.

**Build:**
1. **Decide the canonical state model** — single canonical repo vs. federated with sync contracts. This decision blocks everything downstream; make it deliberately (per the requirements outline and the CRDT research, either is legitimate, but it must be *chosen*, not left ambiguous).
2. **Atomic task-ID allocator** — the compare-and-swap / transactional fix (SQLite `INSERT ... ON CONFLICT` or equivalent).
3. **Git operation lock** — mutual exclusion on writes.
4. **(Optional but high-value) Verify the design first** — before committing to the allocator+lock implementation, write the small TLA+ spec (allocator + lock + 2–3 abstract agents) and run TLC. Either it proves the design race-free or it reproduces the near-deletion interleaving so you can confirm the fix closes it.

**Done when:** two agents cannot obtain the same task ID or write concurrently, demonstrated by a deliberately concurrent test (not just observed absence of failure), and the canonical-state question has a documented answer.

**Sources:** Requirements Outline (Tier 0), Formal Verification (whole doc), Cross-Domain I (CRDTs).

---

## Phase 1 — The Enabling Change: Single Entry Point
*Depends on: Phase 0 (the orchestrator must read correct state).*

This is the structural pivot the whole system hinges on. Almost every later phase plugs into this one point, which is why it comes so early despite not being a "correctness" fix.

**Build:**
1. **Route all operator intent through one orchestrating agent** (HPOM, or whichever agent holds that role). Other agents receive only dispatched, protocol-shaped tasks — never raw operator messages.
2. Keep the orchestrator's job **narrow and mechanical**: interpret → validate against protocol → decompose → route. Not creative. This minimizes the single-point-of-failure risk.
3. **Define each subsystem's interface** ("subsystem API," from Team Topologies) — even informally. This clarifies every boundary before you start building across those boundaries.

**Done when:** you no longer message agents directly; you state intent once to the orchestrator, and it dispatches. There is exactly one place where a task enters the system.

**Sources:** Requirements Outline (VII-ter, Tier 1), Organizational Model (Team Topologies backbone, step 1).

---

## Phase 2 — Visibility: You Can't Improve What You Can't See
*Depends on: Phase 1 (one dispatch point to instrument).*

Deliberately before compliance and resilience, because both of those need to observe behavior to work, and because your original audit existing at all proves MAP couldn't see itself.

**Build:**
1. **Structured logging** — every agent action emits a structured record: actor, action, target, timestamp, causal parent. Not free text.
2. **A trace ID per task** — tag every log line across HPOM/hcom/emergence with a task/session ID written to one place. This gets ~80% of distributed-tracing value without adopting OpenTelemetry.
3. **The shared-state status surface** — the "countdown board": agent status continuously readable from shared state rather than requested via messages. (This also advances Principle 1 and reduces hcom traffic.)

**Done when:** for any task, you can reconstruct the full causal chain of what happened from one place, and any agent's status is readable without asking it.

**Sources:** Requirements Outline (Section V), Cross-Domain II (stigmergy, bullwhip — shared readable state), Index (Principle 1).

---

## Phase 3 — Enforcement: The System Follows Itself
*Depends on: Phase 1 (a point to enforce at) and Phase 2 (the ability to observe compliance).*

Now that there's one entry point and you can see behavior, make the system actually follow its protocol.

**Build:**
1. **The separate verification layer** — a validator (script or dedicated agent) that checks output against the MATOCP spec *before* it's accepted. Never self-reported. This is the single highest-leverage compliance fix. Plug it in at the Phase-1 dispatch point (check once before fan-out).
2. **Schema validation** — reject malformed output structurally rather than trusting formatting.
3. **Jidoka halt authority** — give the validator the four-step loop: detect → **stop (with real authority to halt dispatch)** → fix → mandatory root-cause step that updates the process.
4. **Compliance telemetry** — track *which* rules are violated and how often; track false-positive rate from day one (the AIS lesson).
5. **Periodic protocol re-injection** — re-state core rules at task boundaries to counter instruction decay over long sessions.

**Done when:** protocol violations are caught by the system in real time (not by you in retrospect), the validator can halt on a real problem, and you're tracking both violation and false-positive rates.

**Sources:** Requirements Outline (VII-bis), Organizational Model (Jidoka), Lessons Learned (false-positive ceiling), Cross-Domain III (threshold-gated, safeguarded response).

---

## Phase 4 — Intelligence: Routing and Emergence
*Depends on: Phase 1 (dispatch point), Phase 2 (to measure outcomes), Phase 3 (to validate inferred additions).*

With a safe, observable, self-enforcing spine in place, add the "smart" layers. These are grouped because both are about the orchestrator making better decisions, and both are gated by the same infrastructure.

**Build — Routing (local models):**
1. **Gap score first** — cheap per-task classification of how much is unstated; this also gates how much expensive processing later steps deserve.
2. **Task tiers** — mechanical/deterministic → local; reasoning-heavy/ambiguous → cloud. Route by "does this *need* cloud," defaulting to local.
3. **Fixed lanes for local models** — local *owns* categories (repo scans, diffs, test runs, log triage), with escalation-only fallback to cloud. Route by cognitive load (Team Topologies), not just task type.

**Build — Emergence (in dependency order from its own doc):**
4. **Two-pass inference** — capability pass (what should this have?) then coverage pass (what did it specify?); the gap is the difference.
5. **Reflexion loop with a stable evaluator** — the minimum viable inward self-improvement loop; ground the evaluator in something machine-checkable.
6. **Multi-critic reflection** — Skeptic / Logician / Creative Thinker crew, never one agent grading itself. Highest-leverage emergence upgrade.
7. **End-of-day experiential memory** — batch-compare the day's successes and failures into heuristics for tomorrow. Added last; depends on accumulated trajectory data.

**Done when:** local models receive work by rule (not by you remembering they exist); emergence infers missing requirements above a confidence threshold and routes lower-confidence ones to you as suggestions; and emergence measurably improves over time via the reflection loop.

**Sources:** Requirements Outline (VII-quater), Emergence Design (whole doc), Organizational Model (cognitive-load routing).

---

## Phase 5 — Resilience: Surviving Failure
*Depends on: Phases 2–3 (you must see and contain failures before hardening against them).*

**Build:**
1. **Idempotency keys** on all write operations — retries detected and ignored rather than reapplied.
2. **Dead-letter queue** — failed tasks land somewhere inspectable rather than dropping silently or retrying forever.
3. **Circuit breakers** — stop routing work to a repeatedly-failing agent/subsystem.
4. **Blast-radius partitioning** (Spotify decoupling) — one agent's failure corrupts only its own task's state, not the canonical whole.
5. **Retry/damping discipline** — rate-limit retries and reallocations (ramp metering) to prevent the bullwhip amplification effect through MAP's layers.

**Done when:** killing an agent mid-task, corrupting a message, or forcing a repeated failure results in detection and contained recovery — demonstrated by deliberate chaos testing, not assumed.

**Sources:** Requirements Outline (Tier 5, X.B), Cross-Domain II (bullwhip damping), Organizational Model (blast radius), Cross-Domain III (coagulation — multiple safeguards).

---

## Phase 6 — Governance and the Conservative Anchor
*Depends on: essentially everything above; these are the top-of-stack controls.*

**Build:**
1. **Pre-dispatch approval gates** — high-risk/irreversible actions (deletions, repo-structure changes) require a policy check *before* execution. Optionally a quorum (quorum-sensing pattern) rather than a single check.
2. **Capability whitelisting** — explicit enumeration of what each agent may do (which tools, repos, operations).
3. **Escalation paths** — defined behavior when an agent is uncertain or two agents disagree.
4. **Mittelstand gates on canonical state** — formal documentation and a 5-Whys root-cause discipline for every incident. The deliberately un-agile anchor.

**Done when:** no irreversible action happens without passing a gate; every agent's permissions are explicitly bounded; and incidents produce structured root-cause analysis that updates the process.

**Sources:** Requirements Outline (Tier 6, VII), Organizational Model (Mittelstand + Six Sigma), Cross-Domain II (quorum sensing).

---

## The Critical Path (What Blocks What)

```
Phase 0 (correct state)
   └─> Phase 1 (single entry point)  ← the pivot; most things wait on this
          ├─> Phase 2 (visibility)
          │      ├─> Phase 3 (enforcement)
          │      │      └─> Phase 4 (routing + emergence)
          │      └─> Phase 5 (resilience)
          └─> Phase 6 (governance)  ← sits on top of all of it
```

Phases 0 → 1 → 2 → 3 are a strict chain — each genuinely needs the prior. Phase 4 and Phase 5 can proceed in parallel once Phase 3 exists. Phase 6 is layered on last because governance controls are only meaningful once there's a functioning system to govern.

---

## Sequencing Principles (Why This Order, Generally)

1. **Correctness before cleverness.** No routing intelligence or self-improvement matters if two agents can still corrupt shared state. Phase 0 is non-negotiable first.
2. **Structure before enforcement.** You can't enforce protocol without one place to enforce it (Phase 1 before Phase 3).
3. **Observability before improvement.** Everything that improves the system needs to measure it first (Phase 2 early).
4. **Prove the hardest parts, patch the rest.** Formal verification (TLA+) applies only to the two or three hardest invariants in Phase 0 — not to the whole system. Don't over-invest it.
5. **Threshold-gate the risky, decisive actions.** Emergence auto-additions (Phase 4) and governance gates (Phase 6) both act only above a confidence threshold, with a human in the loop for the middle band.
6. **Add the conservative anchor last, deliberately.** Mittelstand-style formality on canonical state (Phase 6) is added consciously as the un-agile counterweight, once the agile parts exist to be counterweighted.

---

## Minimum Viable MAP (If You Only Do a Fraction)

If the full plan is too much, the smallest version that meaningfully improves on today:
- **Phase 0** (atomic allocator + lock + canonical decision) — closes the incident.
- **Phase 1** (single entry point) — the structural fix that stops manual enforcement.
- **Phase 3, item 1 only** (the verification layer) — catches drift automatically.

Those three alone convert MAP from "held together by operator attention" to "structurally sound with automatic compliance checking." Everything else is refinement on that spine.

---

*Capstone document to the MAP series. Reconciles the local roadmaps in MAP-System-Requirements-Outline.md, MAP-Emergence-Design.md, MAP-Formal-Verification.md, and MAP-Organizational-Model.md into one dependency-ordered plan. Governed by the two design principles in MAP-Index.md.*
