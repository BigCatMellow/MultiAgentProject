# MAP Simulation: A Test Drive Under Ideal Conditions
### An End-to-End Walkthrough of MAP Running As Designed

This document simulates a single task moving through MAP from operator intent to completion, **assuming every improvement from the design series is already built**. It uses the real repository structure (`MAP_System/`, `Projects/Pathwell/`, `map-git`, `validate_task_graph.py`, `TASKS.md`, `AGENTS.md`) and shows each of the twelve documents' mechanisms firing at the moment it would actually fire.

The point is not to prove MAP works — it's to make the *intended* behavior concrete enough that gaps between "this design" and "your current code" become visible. Where the simulation assumes something not yet built, it is flagged **[ASSUMES]** with the phase from the roadmap that would deliver it.

---

## Setup: The World at t=0

**Repository state** (from the real repo):
- `MAP_System/` — the reusable coordination system (canonical).
- `Projects/Pathwell/` — the active writing project, with its own project-local MAP state.
- `TASKS.md` — the task graph, validated by `validate_task_graph.py`.
- Agents launched via `start-all-agents.sh`.

**Agents in play** (ideal-condition roster):
- **HPOM** — the orchestrator; the single entry point. *(Roadmap Phase 1)*
- **Claude-Code-1** — cloud agent, reasoning-heavy work.
- **Ollama-Local-1** — local agent, mechanical work. *(Phase 4 routing)*
- **Validator** — the compliance + event validator, with halt authority. *(Phase 3 / Jidoka)*
- **Emergence** — the inference + self-improvement subsystem. *(Phase 4)*

**The operator's request** (deliberately under-specified, to exercise emergence):
> "Add a word-count feature to Pathwell's editor."

---

## Step 1 — Intake at the Single Entry Point (Phase 1)

The operator sends the request to **HPOM only** — not to both agents directly. This is the restructured command center: one mechanical entry point.

HPOM's first action is not to plan the feature. It is to **write the raw intent to canonical shared state** (`TASKS.md` / the task graph) before anything else reads it. Nothing acts on a relayed copy of the request; everything reads the one authoritative record.

> **Principle 1 in action** (Index): the request becomes a mark on the shared surface, not a message passed agent-to-agent. This is the BIGMAS "centralized workspace as single source of truth" pattern, and the stigmergy model from Cross-Domain II.

---

## Step 2 — Gap Scoring and Emergence (Phase 4, outward)

Before decomposition, HPOM asks **Emergence** for a gap score on the request.

Emergence runs its two-pass inference:
- **Capability pass**: "a word-count feature for a text editor" *should* typically include — live count vs. on-demand, word vs. character vs. page count, selection-only counting, whether it updates on every keystroke or debounced, and a visible UI location.
- **Coverage pass**: the operator specified none of these.
- **Gap score: HIGH.**

Emergence proposes the missing requirements. Each is routed through its **multi-critic self-review** — the Skeptic asks "does a writing app actually need page count?", the Logician checks the proposals don't conflict, the Creative Thinker notes Pathwell's existing quest/gamification system might want word-count *milestones*.

Because the gap score is high, HPOM does not silently build all of this. Per the coagulation-cascade threshold rule, high-confidence inferences (live word count, visible placement) are **auto-added** to the task; medium-confidence ones (milestone integration) are **surfaced to the operator as suggestions**.

> **Principle 2 in action**: emergence idles on weak inferences, commits on strong ones, and keeps a human in the loop for the middle band. *(Emergence Design; Cross-Domain III)*

The operator gets a one-line prompt: *"Auto-adding live word count in the status bar. Suggest also: tie word-count milestones into the existing quest system? [y/n]."* They say yes. The task graph now reflects a complete spec that the original request never contained — MAP's defense against under-specification, the #1 failure mode.

---

## Step 3 — Decomposition and Cognitive-Load Routing (Phase 4, routing)

HPOM decomposes the now-complete task into subtasks and writes them to the task graph, each getting an **atomic task ID** via the allocator.

> **Phase 0 in action**: two subtasks created in the same instant cannot collide on an ID — the compare-and-swap allocator guarantees it. *(Formal Verification proved this design; the near-deletion incident cannot recur here.)*

HPOM routes each subtask by cognitive load and type (Team Topologies + tiering):
- *"Write the word-counting logic (pure function, handles unicode/whitespace edge cases)"* → **Claude-Code-1** (reasoning-heavy, edge cases).
- *"Add the status-bar UI element and wire it to the count"* → **Claude-Code-1** (touches app structure).
- *"Run the existing test suite and report failures"* → **Ollama-Local-1** (mechanical, owns this lane outright).
- *"Scan the repo for existing word-count or counting utilities to reuse"* → **Ollama-Local-1** (repo scan, its fixed lane).

> **Phase 4 in action**: the local model gets real work by rule, not by the operator remembering it exists. Each subtask carries alignment (the *what/why*) but leaves the *how* to the agent (Spotify matrix). *(Organizational Model)*

---

## Step 4 — Execution With a Lock (Phase 0 + Phase 5)

Claude-Code-1 begins the UI subtask, which modifies shared editor files. Before writing, it acquires the **git operation lock** via `map-git`.

Ollama-Local-1's repo scan finishes and finds no reusable counting utility — it writes that result to shared state (not a message to Claude-Code-1; a mark on the board). Claude-Code-1, reading shared state, sees "no existing utility" and proceeds to write a new one, without the two agents ever directly communicating.

> **Principle 1 again**: coordination happened through shared state (the "entanglement"/CRDT idea, the subway countdown board), not point-to-point chatter. Zero hcom traffic was needed for the two agents to stay consistent.

Every write carries an **idempotency key**. When Ollama-Local-1's test-run subtask times out and retries, the retry is recognized and does not double-post results. *(Phase 5)*

---

## Step 5 — The Validator Fires (Phase 3 / Jidoka)

Claude-Code-1 submits its word-counting function. The **Validator** checks it against the MATOCP schema *before* it's accepted into canonical state — not self-reported by the author agent.

Two things happen:
- **Schema check passes**: the output is shaped correctly.
- **A content check flags an anomaly**: the function counts "word — word" (em-dash without spaces) as one word, which for a *writing* app is likely wrong.

This single anomaly, from one agent, is below the response threshold — it's noise-level. The Validator notes it but does not halt. *(Coagulation threshold: one isolated signal ≠ system-wide response.)*

Then a **second** correlated signal arrives: the milestone-integration subtask reports the same miscount breaks quest-progress tallies. Now the anomaly is **correlated across two subtasks** — it crosses the threshold in both magnitude and spread.

The Validator invokes **Jidoka**:
1. **Detect** — the miscount appears in two places.
2. **Stop** — it halts acceptance of the affected subtasks (it has the authority to do so).
3. **Fix** — routes the counting function back to Claude-Code-1 with the specific failing case.
4. **Root cause** — logs a 5-Whys entry: the spec never defined tokenization rules → emergence's capability pass didn't include "define word boundary rules" → *that becomes a new item in emergence's end-of-day learning.*

> **Principle 2, fully expressed**: idle on the single noise signal, respond decisively on the correlated one, and the response is safeguarded (it re-routes rather than nuking state). *(Organizational Model / Jidoka; Cross-Domain III)*

---

## Step 6 — Observability Throughout (Phase 2)

Every step above emitted a structured event tagged with the task's trace ID: intake, gap score, each allocation, each lock acquire/release, the validator halt, the re-route. The operator can open one view and see the entire causal chain — *"the halt at 14:32 traces back to an under-specified tokenization rule at intake"* — without reconstructing anything by hand.

> This is the difference from the world that produced the original audit: MAP saw its own failure in real time, with the causal chain intact. No retrospective archaeology. *(Requirements Outline §V; the "self-auditing" target.)*

---

## Step 7 — Completion and Governance (Phase 6)

Claude-Code-1 fixes the tokenization, re-submits, the Validator passes it, and the subtasks are accepted into canonical state. HPOM prepares to merge to `MAP_System`/Pathwell.

Because a merge to canonical state is an **irreversible-ish action**, it passes a **pre-dispatch approval gate**: `validate_task_graph.py` must pass, and the change requires the operator's confirmation (or a validator quorum). The gate passes. `map-git` commits.

> **Phase 6 / Mittelstand anchor**: the one part of the flow that is deliberately conservative — formal gate, validation, documentation — because this is exactly where the near-deletion incident originally happened. *(Organizational Model)*

---

## Step 8 — End of Day (Phase 4, inward)

That night, **Emergence** runs its ExpeL-style batch reflection over the day's tasks. It notices a pattern: **three of today's tasks involved text processing, and all three under-specified tokenization/boundary rules.** It distills a new heuristic into its memory:

> *"For any text-processing feature, the capability pass must include explicit tokenization/boundary-rule definition."*

Tomorrow, the word-boundary gap that caused today's halt will be caught at intake, before any code is written.

> **The cybernetic loop closes** (Wiener, Philosophical Foundations): the system observed the gap between intended and actual behavior and corrected its own process. It is measurably better tomorrow than today, with no retraining — just accumulated, distilled experience. *(Emergence Design)*

---

## What This Test Drive Reveals

Running the simulation surfaces exactly where your real repo is versus this ideal. Checklist form:

| Step | Mechanism | Roadmap Phase | Likely status in current repo |
|---|---|---|---|
| 1 | Single entry point (HPOM only) | Phase 1 | **Check**: do you still message agents directly? |
| 2 | Gap scoring + multi-critic emergence | Phase 4 | **Likely partial**: emergence exists; multi-critic self-review probably not |
| 3 | Atomic task ID allocation | Phase 0 | **The P0**: is `validate_task_graph.py` backed by an atomic allocator? |
| 3 | Cognitive-load routing to Ollama | Phase 4 | **Check**: does local get work by rule, or sit idle? |
| 4 | Git lock via `map-git` | Phase 0 | **Check**: does `map-git` enforce mutual exclusion, or just wrap git? |
| 4 | Coordination via shared state, not messages | Principle 1 | **Check**: how much hcom traffic is really point-to-point? |
| 5 | Validator with Jidoka halt authority | Phase 3 | **Likely gap**: can your validator *halt*, or only log? |
| 6 | Structured tracing with trace IDs | Phase 2 | **Likely gap**: can you see one causal chain end-to-end? |
| 7 | Pre-dispatch approval gate on merges | Phase 6 | **Check**: is canonical-state merge gated or improvised? |
| 8 | End-of-day experiential learning | Phase 4 | **Likely not built**: the inward self-improvement loop |

The **"Check"** and **"Likely gap"** rows are your actual near-term backlog — the places where the ideal simulation diverges from what `start-all-agents.sh` launches today.

---

## Suggested Next Step

Pick **one step** of this simulation and instrument your real repo to log whether it currently behaves this way. Step 4 (coordination via shared state vs. messages) and Step 5 (can the validator actually halt?) are the two highest-signal probes — they tell you fastest whether MAP is already living by its two core principles or just documented to.

If you want, the next artifact could be a small **Python simulation harness** that actually runs this eight-step flow with stub agents — printing the trace, exercising the allocator under concurrency, and deliberately triggering the Step-5 halt — so you can watch the ideal flow execute and then swap stubs for real agents one at a time.

---

*Companion document to the MAP series. Exercises every phase of MAP-Implementation-Roadmap.md against the real repository structure. Governed by the two design principles in 00-MAP-Index.md.*
