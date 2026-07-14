# MAP: The Synthesized System
### One Specification, Built From the Best Lesson of Every Part

This is the single, definitive MAP — not a menu of options, not another version to compare. It is the one system that results from taking everything explored (the orchestration frameworks, the organizational models, the cross-domain research, the philosophical foundations) and keeping only what survived being tested. Every component below is annotated with **the one source it took its most durable lesson from**, because the whole premise is that no single system had the answer — but each had a part worth learning from.

Where the simulation overruled the theory, the simulation wins, and it's marked **[proven]**. Where a plausible idea was cut because it made things worse, it's listed at the end with what taught us.

---

## What MAP Is (the frame that makes everything else fall into place)

MAP is a **coordination system that happens to use AI agents as workers** — not an AI system. Its hard problems are concurrency, authority, communication, and control: problems that distributed systems, organizational theory, and even biology solved long before language models existed. The work was never invention. It was translation: finding the field that already solved each piece, and taking its answer.

> *Learned from:* the reframe itself (the Thesis) — treating MAP as management/distributed-systems rather than AI is what made every other solution findable.

---

## THE SYSTEM

### 1. One Entry Point — the Orchestrator (HPOM)
All operator intent flows through a single orchestrating agent whose job is narrow and mechanical: interpret → validate against protocol → decompose → route. Other agents never receive raw operator messages, only dispatched, protocol-shaped tasks. Keeping the orchestrator's job mechanical (not creative) minimizes the single-point-of-failure risk.

> *Learned from:* the **orchestrator-worker pattern** (Anthropic's "Building Effective Agents," ~70% of production multi-agent systems). *Confirmed by simulation:* never a cost problem across any run; it's the structural backbone every other mechanism plugs into.

### 2. One Canonical State — Directly Readable, Not Relayed
A single authoritative store holds what is true right now. Agents coordinate by **reading and writing this shared surface**, never by passing status through point-to-point messages. Two agents working on related tasks stay consistent because they observe the same ground truth, not because they talk.

> *Learned from:* the **convergence of three independent domains** — stigmergy (ants coordinate via marks on a shared environment), the bullwhip effect (relayed signals amplify into chaos across layers), and Kuramoto synchronization (coherence from observing shared local state). Independently confirmed in 2026 research (BIGMAS: "centralized workspace as single source of truth… no point-to-point communication"). The **standardized message/task format** agents read and write (MATOCP) is best understood through **intermodal shipping containers**: a fixed, standard interface that any content can travel inside and any carrier can handle — the container is what lets ships, trains, and trucks interoperate without renegotiating the cargo each time, exactly as a stable schema lets heterogeneous agents interoperate without bespoke parsing. *Confirmed by simulation:* zero point-to-point messages were ever needed; agents stayed consistent through shared-state reads alone.

### 3. Atomic Allocation + a Cross-Process Lock — the Correctness Floor
Task IDs are allocated atomically (compare-and-swap / a single transactional writer). Writes to canonical state are mutually exclusive. **The lock must be cross-PROCESS (an OS-level file lock), not a thread lock and not a bare git wrapper** — because MAP's real risk is separate agent processes touching the same files, where an in-process lock would pass every test and still fail in production.

> *Learned from:* **distributed-systems fundamentals** (compare-and-swap, mutual exclusion, optimistic vs. pessimistic concurrency), reinforced by two transit-safety models that map almost exactly: **railway block signaling** for the lock (a train physically cannot enter a block another train occupies — mutual exclusion by construction, not by hoping), and **flight-level separation** for allocation (aircraft are assigned discrete, non-overlapping altitudes so two can never occupy the same space — exactly what atomic non-colliding task IDs do). *Corrected by simulation:* a sequential test showed "safe" but was too weak; modeling the race at process level produced **599 collisions out of 600 allocations** when unlocked, and revealed that Python's GIL means the danger was never thread-level. This is the direct fix for the near-deletion incident.

### 4. The Validator — Halt Eagerly, but Be Accurate
Every agent output is checked by a separate component (never self-reported by the author), built as a **layered cascade**: **Layer 1** runs all deterministic checks (schema, types, parse, tests, invariants) — ground truth, near-zero false positives; **Layer 2** is a fuzzy judge (LLM-as-judge) that inspects only what passed Layer 1 for *semantic* defects (well-formed but logically wrong). On a real anomaly the validator **halts on the first signal** — it does not wait for a second correlated signal. When it halts, it runs the four-step loop: **detect → stop (with real authority) → fix → mandatory root-cause** that updates the process so the failure can't recur.

Its viability depends on **accuracy: the false-positive rate must be kept near ~1%** — but a direct test corrected a key assumption here. The layered architecture delivers high *catch* cheaply (deterministic coverage drives catch from 75% to 99%), but it does **not** deliver the ~1% false-positive target on its own: false positives come almost entirely from Layer 2 firing on clean output, and they track the judge's *intrinsic* accuracy, not the architecture (an 8%-accurate judge yields ~8% overall regardless of how good Layer 1 is). Hitting ~1% therefore requires solving **judge accuracy** directly — via cited/checkable reasons (a judge must point to a re-verifiable claim, not "seems wrong"), ensembling for high-severity only, threshold calibration against labeled data, and learning from overridden false halts. See the Validator Specification for the full design; the honest status is that the architecture is specified and its catch is tested, but the ~1% false-positive assumption is a *specified open problem*, not a solved one.

> *Learned from:* the halt-and-root-cause loop is **Jidoka** (Toyota Production System); the separate-checker-not-self-report is the **kitchen expediter** (no station reports its own doneness); the accuracy requirement is the **Artificial Immune Systems** false-positive ceiling (a noisy detector gets ignored). *Corrected by simulation — this is the single most important correction:* the design's instinct toward **threshold gating** (idle on noise, act only on correlated signals, from quorum sensing and the coagulation cascade) was **proven actively harmful** — threshold=2 caught only 47% of defects vs. 100% for eager halting, robust even when a false halt costs 4× a shipped defect. Threshold gating was a workaround for an inaccurate validator; the correct fix is to halt eagerly and drive false positives down directly. Eager halting keeps operator trust *only if* it's accurate — at ~1% false positives, trust holds and catch stays at 100%; at 5%, trust erodes and real catch silently falls to ~79%.

### 5. Emergence — Infer the Unstated, Then Watch Yourself
Two jobs, one architecture over the shared workspace:

**Outward (fill the gaps):** every task gets a **gap score** first (how much is unstated), which gates how much effort the rest deserves. Then a **two-pass inference** — what capabilities *should* this have, then which did the request specify; the difference is the gap. High-confidence inferences are auto-added; only genuinely uncertain ones are surfaced to the operator. **Routine capabilities are auto-added, not queried.**

**Inward (improve the process):** a **multi-critic self-review** (a Skeptic, a Logician, a Creative Thinker — never one agent grading its own homework, which gets stuck in "degeneration of thought"), plus **end-of-day learning** that compares the day's successes and failures and distills recurring misses into heuristics for tomorrow. Critically, this learning must be **bounded by a pruning guard**: any learned heuristic that keeps firing but never actually prevents a defect is spurious (learned from a misattributed miss) and must be pruned. Unbounded learning is not safe — it is the same over-learning failure that got pre-tokenization cut, arising from the loop's own dynamics.

> *Learned from:* gap-scoring from **implicit-need inference research** (AURA); two-pass from **requirements-engineering pipelines**; multi-critic from **Multi-Agent Reflexion**; end-of-day learning from **ExpeL**; the whole inward loop is **Wiener's cybernetic feedback** made concrete. *Corrected by simulation (twice):* first, a single miscalibrated confidence value (treating the routine capability "edge_cases" as uncertain) was generating **65% of all operator interrupts** — recalibrating routine caps to auto-add dropped operator pestering from 83 per 100 tasks to 28, with no loss in catch. Second, a longitudinal (40-day) test showed the learning loop **converges fast (defects → 0 by day 5) but over-learns without a pruning guard**: misattributed defects create permanent spurious heuristics that inflate steady-state cost, and the damage grows sharply with noise (unguarded cost climbs from 85 to 154 as misattribution rises to 60%, while guarded stays near 87). *Confirmed:* end-of-day learning removes recurring defect classes and is a net win — *provided* it prunes heuristics that fire but never prevent a defect. The guard is slightly wasteful at very low noise and essential at realistic noise.

### 6. The Agent Roster and Routing — Owned Lanes Across Three Tiers
MAP defines a **fixed roster of agents at startup, each owning a lane** (a category of work), and routes by whether a task *needs* what a higher tier provides — defaulting work downward. The roster spans three tiers with deliberately different cost profiles:

- **Reasoning tier** — Claude Code / top-tier models, 1–2 agents. Hard, multi-step, ambiguous work and anything orchestration-adjacent.
- **Cheap-language tier** — low-level Claude (Haiku-class), several, via API. Mechanical work that still needs a real language model: log triage, first-pass drafts, summarization, simple edits, **and the Library agent (component 9) that maintains the wikilinked, summarized knowledge corpus.** Cheap and fast enough to run many in parallel.
- **Free-mechanical tier** — Ollama / local models. The truly deterministic, offline-capable, private lane: repo scans, file diffs, test execution, formatting. Zero marginal cost, no API needed.

**Pre-spawning is right for some tiers and wrong for others** — the two agent types have opposite cost profiles, so treat them differently:
- **API workers (both Claude tiers): register the full roster at startup, generously.** An idle API role costs nothing — you pay per token only when it works — so define as many owned lanes as useful up front.
- **Local (Ollama): budget by memory, not enthusiasm.** Each resident model consumes RAM/VRAM and competes for it on one machine. Keep one or two warm (via keep-alive) and spin the rest up on demand. "Spawn all local models at startup" is the wrong move *specifically* because of memory contention.

**The critical correction — spawning is not the fix for underutilization.** An idle spawned agent is just an idle agent with a name. Local models sit unused not because they're unavailable but because, without a routing rule, the orchestrator defaults every task *up-tier* to the most capable agent. The fix is the **rule**: mechanical work defaults down-tier, and each agent owns its category outright, so the router always has somewhere to send work that isn't the top tier. Pre-spawning is complementary; the routing rule is what earns the utilization.

**One failure mode to avoid:** don't make a role so narrow it's a single task ("Agent 3 = test runner only"). If no test work arrives, Agent 3 is idle and the idleness is now *structural* — worse than before. Each role is an owned **lane** (a category), not one job. And because every agent registers at startup with its status on the shared board (see Observability), unused ready capacity becomes **visible and routable** — which is what makes the routing correction actually happen instead of being forgotten.

> *Learned from:* **Team Topologies** — cognitive load as the organizing constraint (an agent, especially a small local one, has a finite context ceiling; route to keep each under it); the **hospital-triage** model (the nurse practitioner owns a category, not a lesser status); and the subway **express-vs-local** distinction (riders pick the train their destination needs, not the fanciest one — reasoning/cheap-language/free-mechanical map to express/limited/local). *Corrected by simulation:* elaborate "strict routing" (forcing all hard work to cloud) was **proven to have zero effect** and was cut — once the validator catches everything, where a defect originated is irrelevant to what ships. The simulation also confirmed the deeper point: **availability was never the bottleneck; the routing rule was.**

### 7. Governance — A Gate Where It's Irreversible, and a Conservative Anchor
Irreversible or high-risk actions (deletions, canonical-state merges, repo-structure changes) pass a **pre-dispatch approval gate** before execution — optionally requiring a quorum of checks rather than one. Canonical state specifically is governed conservatively: formal documentation, a validation gate (`validate_task_graph.py` must pass), and a structured **5-Whys root-cause** on every incident. This is the deliberately un-agile part, because it's exactly where the near-deletion incident happened.

> *Learned from:* the approval gate echoes **quorum sensing** (act only past a threshold of agreement) and **emergency-vehicle signal preemption** (flagged actions can preempt); the conservative anchor is **German Mittelstand / Six Sigma** engineering culture. Capability whitelisting (each agent's permitted tools/repos enumerated) closes the most common "system design" failure in the taxonomy.

### 8. Observability — The Layer That Makes Everything Else Possible
Every action emits a structured record (actor, action, target, timestamp, causal parent), and every step carries a **trace ID** so the full causal chain of any task is readable from one place. Agent status lives on the shared surface, continuously readable rather than requested.

> *Learned from:* **OpenTelemetry** span/trace concepts and the subway **countdown board** (broadcast status, don't answer queries). *Confirmed by simulation — decisively:* this near-zero-cost layer is what made every tuning decision measurable. Without it, none of the corrections above could have been found. The fact that MAP originally needed a manual audit to see its own failures is the exact gap this closes.

### 9. The Knowledge Layer — a Library Agent Over a Wikilinked, Summarized Corpus
MAP's notes, mds, and skill files are not a flat pile every agent reads end-to-end. They form a **linked knowledge graph** via wikilinks (`[[...]]`), and each file has a **compact summary** that agents load by default, traversing to full detail only when they actually need it. A dedicated **Library agent** owns this layer: it maintains the links, generates and updates the summaries, and serves the right slice of knowledge on request.

This exists because "coordinate through shared readable state" (Principle 1) only works if that state is readable *cheaply*. A shared surface made of full-length documents that every agent must read completely is the opposite of the cognitive-load principle — it drowns agents in context and burns tokens. The Library agent is what makes the shared knowledge surface compact and navigable instead of exhaustive.

**Three jobs, one agent:**
- **Wikilinks as connective tissue** — documents reference each other explicitly (`[[schema-pin]]`, `[[TASK-023]]`), so the corpus is traversable and the system can reason about how pieces relate, not just read them in isolation. This is the Christopher Alexander *pattern-language* idea realized: patterns that cite the patterns they depend on and conflict with.
- **Summaries for context economy** — a short version loads by default; the full text is one link away. This is the document-layer expression of the existing `context-pruning.md` / `schema-pin.md` work.
- **Serving, not working** — the Library agent doesn't do task work; it reduces every other agent's cognitive load by returning compact, linked context on demand.
- **Hierarchical addressing for retrieval** — the Library agent routes a request to the right knowledge the way a postal system routes mail: coarse-to-fine address resolution (domain → topic → file → section) rather than scanning everything. A well-structured wikilink namespace *is* this address space, which keeps retrieval cheap as the corpus grows.

**Where the knowledge and learned heuristics actually live (a real gap the rest of the system hand-waves):** the Library agent's corpus and emergence's end-of-day heuristics need a persistence layer, not just "memory." This is the same WAL-mode SQLite store used for canonical state (Implementation Notes), optionally fronted by a purpose-built agent-memory system. This should be a *deliberate, evaluated* choice — see the companion tool-evaluation appendix — not an unstated assumption, because where memory lives determines whether learned heuristics survive restarts and whether the summary cache can track staleness.

**Two failure modes it must be designed against** (a Library agent is a new mechanism — per the Braess discipline, it must earn its place, not just be assumed useful). *Simulation tested this component directly and the result is emphatic: the full design cuts context cost 34–85% across every regime, but a partial build is a net loss — a library with summaries alone, no wikilinks and no staleness tracking, is **more expensive than having no library at all**, because stale/lossy defects cost more than the reads save.*
- **Summary staleness / drift — THE load-bearing concern.** If a file changes after it was summarized, agents read a summary that now lies. This is a cache-invalidation problem, tied to the event layer: a file write emits an event, the Library agent sees it, the summary is marked stale and regenerated. *The simulation's central finding: event-driven staleness invalidation is the single feature doing almost all the work — it's what turns the layer from a liability into an 80% cost cut, and it matters more as file churn rises. It is not one of two optional mitigations; it is the non-negotiable core.* A summary that doesn't track its source's changes is worse than no summary.
- **The summary hides the needed detail** — a shortened file is lossy by definition; an agent deciding off a summary that omitted the critical point is the exact under-specification failure emergence fights, now self-inflicted. The mitigation *is* the wikilink graph: keep the summary compact but always link to full detail, so an agent that needs more traverses to it rather than being stuck with the lossy version. **Compact summary + wikilinks to full detail + staleness tracking** is the shape that makes this a real cognitive-load reduction rather than a new source of drift.

**Two conditions the simulation identified for the layer to pay off** (watch these; outside them, reconsider the component):
- **Real compression (≥ ~1.5×).** If summaries aren't meaningfully smaller than the full docs, the scheme loses its point — break-even is around 1.2× compression. In practice summaries run 5–20× smaller, comfortably clear, but if a "summary" ever creeps toward the size of its source, that file shouldn't be in the summarized set.
- **Cheap-tier regeneration.** Re-summarizing on the cheap-language tier costs ~57% less than on the reasoning tier for the same work — summary maintenance is mechanical and must not run on an expensive agent.

**Scope:** the wikilink graph and summaries cover MAP's own system docs and skill files (the internal knowledge agents operate by). Whether it also extends to a project's content (e.g. Pathwell's notes) is a separate, opt-in decision — as MAP-internal infrastructure the Library agent's default remit is the system's own knowledge, not project deliverables.

> *Learned from:* **Christopher Alexander's *A Pattern Language*** (named, cross-referenced patterns that link to their dependencies — the direct ancestor of software design patterns) for the wikilink graph; **ZIP-code / postal hierarchical addressing** for the retrieval-routing logic (coarse-to-fine resolution instead of a flat scan); **Team Topologies** for the Library agent as a *platform/enabling* role (it absorbs cognitive load off working agents, exactly the meta-principle applied to knowledge); the existing `context-pruning` / `schema-pin` skill work for the summarization discipline; and the **event-sourcing / causal_edges** storage layer (Implementation Notes) for staleness tracking. *Cost profile:* summarization and link-maintenance are "mechanical but need a real model" — this belongs on the **cheap-language tier**, not a top-tier reasoning agent.

---

## THE META-PRINCIPLES (the through-lines that tie it together)

**A. Absorb cognitive load off the unit doing the valuable work; give that unit alignment on the goal and autonomy on the method.**
The orchestrator, validators, and emergence all exist to keep the working agent's load under its ceiling. Each agent gets a clear *what/why* but freedom over *how*.
> *Learned from:* **Team Topologies** (load absorption) + the **Spotify alignment/autonomy matrix** (the durable half of a mostly-discarded model).

**B. Coordinate through shared truth; gate the irreversible; halt eagerly but accurately.**
The two convergent design principles, corrected by evidence: shared-state coordination (proven, zero messages) and threshold-free-but-accurate control (the biggest correction — eager halting beats threshold gating when accuracy is high).

**C. Adding a mechanism usually makes it worse. Prove each addition earns its place.**
> *Learned from:* **Braess's Paradox** — observed live three separate times in simulation (threshold gating, strict routing, peer review all made MAP worse). This is the discipline that keeps the system simple.

**D. No written rule enforces itself; no competent behavior fully reduces to rules.**
Why a separate verification layer is structural, not a documentation fix, and why escalation paths to a human are necessary, not optional.
> *Learned from:* **Wittgenstein** (rule-following paradox) + **Polanyi** (tacit knowledge).

**E. A controller must be at least as complex as what it controls.**
The orchestrator must have enough variety to actually govern its agents; if it's simpler than their combined behavior, it fails by necessity, not carelessness.
> *Learned from:* **Ashby's Law of Requisite Variety**; the recursive-autonomous-subsystem shape is **Beer's Viable System Model**.

---

## WHAT WAS DELIBERATELY CUT (and what taught us it was wrong)

| Cut mechanism | Sounded right because | What proved it wrong |
|---|---|---|
| **Threshold gating on the validator** | Quorum sensing & coagulation cascade — idle on noise, act on correlated signal | Simulation: 47% catch vs. 100% for eager halting; a software defect's first occurrence is already real, not noise |
| **Strict/forced routing** | Higher-skill agents should get hard work | Simulation: zero effect on what ships |
| **Pre-emptive capability injection** (e.g. always pre-define tokenization) | Kill the under-spec defect class at the source | Simulation: net-negative — adds work for defects the validator already catches |
| **Peer-review pass** | Defense in depth; a second reader catches more | Simulation: net-negative once modeled realistically (you don't know which outputs to review in advance) |

Every one of these was a plausible, well-motivated idea. Each made MAP measurably worse. Keeping the system honest meant cutting them — which is the whole point.

---

## IMPLEMENTATION NOTES — Concrete, Proven Tools for the Hard Parts

The two components the simulation flagged as make-or-break (the cross-process lock and durable canonical state) have well-established, boring, proven solutions. Use them rather than hand-rolling — hand-rolled locking is exactly what produced the near-deletion incident.

### The cross-process lock → the `filelock` library
Python's standard `threading.Lock` is useless here (it's in-process only), and raw `fcntl.flock` has a notorious footgun: **the lock is tied to the open file descriptor, so if you close the file the lock silently releases** — a subtle bug that would let the race back in. The maintained `filelock` library wraps the OS primitives correctly (fcntl on Unix, msvcrt on Windows, with a soft-lock fallback) behind a context manager that releases safely even on error:

```python
from filelock import FileLock
lock = FileLock("map_state.lock")
with lock:                     # cross-PROCESS mutual exclusion
    tid = allocate_next_id()   # the read-compute-write critical section
    write_task_row(tid, owner)
```

Notably, `filelock` also ships a **SQLite-backed reader/writer lock** (multiple readers, single writer) and an **NFS/HPC variant with TTL-based stale-lock detection across hosts** — directly relevant to MAP's "one canonical state, many readers" shape, and to crash-safety (a process that dies holding a lock must not wedge the system forever). This is what `map-git` should wrap.

### Durable canonical state → SQLite in WAL mode, single-writer
The canonical store should be SQLite with **`PRAGMA journal_mode=WAL`** set once (it persists in the file header). This is the single strongest concurrency knob: readers and the writer stop blocking each other, and crash recovery becomes automatic. But WAL does **not** grant multiple writers — SQLite still serializes writes, and firing concurrent write transactions produces `SQLITE_BUSY` / "database is locked" errors. The proven pattern, confirmed across multiple production write-ups (SkyPilot, others), matches what MAP already specifies:

- **One dedicated writer** (a single process/thread) owns all writes; everything else enqueues write-jobs to it. This *is* the single-entry-point orchestrator, expressed at the storage layer — the architecture and the database pattern reinforce each other.
- **`PRAGMA synchronous=NORMAL`** with WAL: durable against application crashes, with only a millisecond-scale rollback risk on full power loss — the right tradeoff for a home system.
- **A high `busy_timeout`** so brief write contention waits rather than erroring.

A 2026 research system (Operational Memory Architecture) independently lands on nearly MAP's exact schema for this: an immutable **event** table, a **causal_edges** table (the trace-tree / causal-parent links from the Observability component), and a **snapshot** table of serialized state — all in WAL-mode SQLite. That's the event-sourcing + tracing layer MAP wants, validated as a real architecture, buildable with the standard library alone.

> *Learned from:* the **`filelock`** library and its SQLite/NFS lock variants; **SQLite WAL** production practice (SkyPilot's "abusing SQLite to handle concurrency," multiple 2025–2026 benchmarks); and the **Operational Memory Architecture** paper (arXiv:2605.18755) for the event/causal/snapshot schema. *Why it matters:* these are the concrete, dependency-light building blocks for the two requirements the simulation proved are non-negotiable — and every one of them independently converges on MAP's single-writer, shared-readable-state design.

---

## BUILDING IT (the order that respects dependencies)

The dependency logic: *you can't enforce what you can't route through one point; you can't route safely without correct state; you can't know state is correct without seeing it.*

1. **Correct, singular state** — canonical-state decision, atomic allocation, the cross-process lock. *(The floor. Closes the incident. Optionally prove the design in TLA+ first.)*
2. **Single entry point** — route all intent through the orchestrator. *(The pivot everything plugs into.)*
3. **Observability** — structured logging + trace IDs. *(Early, because everything downstream needs to be measurable.)*
4. **The validator** — eager halt, high accuracy, Jidoka loop. *(Now that there's one point to enforce at and the means to see compliance.)*
5. **Emergence + basic routing + the Library agent** — gap-scoring, multi-critic review, cognitive-load split, and the wikilinked/summarized knowledge layer. *(The intelligence and knowledge economy, on the safe spine. The Library agent depends on the event layer from step 1 for staleness tracking.)*
6. **Resilience** — idempotency keys, dead-letter queue, blast-radius containment. *(Harden against failure you can now see and contain.)*
7. **Governance** — approval gates, whitelisting, the Mittelstand anchor. *(Top-of-stack controls, once there's a working system to govern.)*

**If you build only three things:** the cross-process lock (step 1), the single entry point (step 2), and the accurate eager validator (step 4). Those convert MAP from "held together by operator attention" to "structurally sound and self-checking." Everything else is refinement on that spine.

---

## The One-Paragraph Version

MAP is a coordination system with AI workers. Route everything through one mechanical orchestrator; keep one canonical state that agents coordinate through by reading, not messaging; protect it with a cross-process lock; check every output with a separate validator that halts eagerly but stays accurate; let an emergence layer infer what tasks leave unsaid and improve itself by watching its own misses; keep the system's own knowledge as a wikilinked, summarized corpus served by a Library agent so agents load compact context cheaply; run a fixed three-tier roster (reasoning / cheap-language / free-mechanical) where each agent owns a lane and mechanical work defaults down-tier by rule; gate the irreversible; and make all of it visible through structured tracing. Take the best-proven lesson from each field that faced this problem before — orchestration frameworks, Toyota, Team Topologies, distributed systems, immunology, Wittgenstein, Ashby — and cut every clever addition that measurement shows makes it worse. That is the best MAP: not the most sophisticated one, but the one where every part earned its place.

---

*The definitive synthesis. Supersedes the experimental simulation versions (map_v1–v7), whose conclusions are now baked into this specification. Draws on the full MAP document series and the two rounds of simulation results.*
