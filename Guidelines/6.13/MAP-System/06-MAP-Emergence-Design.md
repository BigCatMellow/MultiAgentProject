# MAP Emergence & Instinct Subsystem: Design
### Requirement Inference and Self-Improvement for MAP's Gap-Filling Layer

This document specifies the emergence/instinct subsystem — the part of MAP that infers unstated requirements ("a word processor needs a save feature") and, turned inward, finds its own weak points and improves. It has two halves that share one architecture: an **outward** half (inferring what a task is missing) and an **inward** half (inferring what the inference process itself is missing).

Both halves are grounded in current (2025–2026) research on implicit-need inference and self-improving agents. Where a claim comes from that literature, the source is named.

---

## 0. Why This Subsystem Matters Most

The MAST failure taxonomy (Cemri et al., 2025) found that **under-specification is the single most common multi-agent failure mode** — around 15% of all breakdowns. Emergence is MAP's direct defense against that failure. Improving it is not a feature enhancement; it is hardening MAP's largest statistical weak point. This is the reason to invest here before more speculative work.

---

## PART ONE — OUTWARD: Inferring What a Task Is Missing

### 1. Make Gap-Detection an Explicit, Separate Step
Do not treat gap-finding as a byproduct of generation ("also think about what's missing"). The AURA approach (arXiv:2606.05557) factors gap estimation out as its own **pre-execution routing decision**: it infers the gap between the literal request and the plausible real need, emits a **scalar gap score**, and uses that score to decide how much effort to spend probing for missing pieces before acting.

**For MAP**: every incoming task gets a gap score first.
- "Make a word processor" → high gap (much unstated: save, undo, autosave, markdown, file formats)
- "Add a 4px margin to the save button" → low gap (little to infer)

The gap score then controls how hard emergence looks, and — importantly — how much of the expensive self-review (Part Two) is worth running. High-gap tasks earn deep inference; low-gap tasks pass through cheaply.

### 2. Split "What's Needed" From "What's Present" Into Two Passes
A classification-then-extraction pipeline (arXiv:2606.13082) outperformed single-pass approaches by separating detection from filling.

**For MAP**, emergence runs two passes:
1. **Capability pass**: given the task type ("word processor"), classify which standard capabilities the artifact *should* have — a checklist generated from domain knowledge (save, load, undo/redo, autosave, markdown, export, find/replace…).
2. **Coverage pass**: check which of those the instruction actually specified.
3. The **gap** is the set difference — what's needed but not covered.

This is more reliable than asking one pass to simultaneously brainstorm and audit, because the two cognitive tasks interfere with each other when combined.

### 3. Use a Small Crew, Not One Inferrer
The MARE framework (multi-agent requirements engineering, via ScienceDirect RE survey 2026) used specialized agents over a shared workspace and beat single-agent setups on requirement completeness.

**For MAP**, emergence is itself a small crew sharing one workspace (Principle 1 — shared state over messaging):
- One agent **proposes** missing requirements
- One agent **verifies** each proposal is actually warranted (guards against over-adding)
- One agent **checks consistency** across the proposed additions

### 4. Keep Design-Time and Runtime Separate
The 4D-ARE paper (Tencent, 2026) makes the sharp distinction: runtime reasoning frameworks (ReAct, chain-of-thought) *assume a well-specified task*, and "in practice that assumption is almost never met." Emergence is doing **design-time specification repair** — inferring what the task *should have said* — which is a different activity from the agents' runtime reasoning about *how* to execute. Keeping these conceptually distinct is what makes emergence a real subsystem rather than just "smarter prompting."

### 5. The Honest Limit
LLM-based requirements extraction captured only about **half** of all real requirements by F1-score in one evaluation (ScienceDirect RE survey), with quality highly dependent on prompting and human validation. Emergence will have both false negatives (misses real needs) and false positives (adds unwanted features).

**Mitigation** (the coagulation-cascade pattern from Cross-Domain Vol. III): only **auto-add** an inferred requirement when confidence crosses a threshold; route lower-confidence inferences to the operator as *suggestions* rather than silently building them. Idle on weak signals, act decisively on strong ones, and keep a human in the loop for the middle band.

---

## PART TWO — INWARD: Finding Its Own Weak Points

Turning emergence on itself produces a self-improving loop. The research splits cleanly into two timescales that match the two you asked about: **as-we-go** (real-time correction) and **end-of-day** (batch consolidation).

### 6. As-We-Go: The Reflexion Loop
The Reflexion pattern (Shinn et al., 2023, now a standard architecture) improves behavior **without retraining** — the agent reflects on failure in natural language, stores the reflection in memory, and conditions its next attempt on it. Three roles:
- **Actor** — does the work (emergence inferring requirements)
- **Evaluator** — scores the output. Crucially this can be cheap: a heuristic ("did the operator have to manually add something emergence missed?"), a check for loops, or an LLM judging quality
- **Reflector** — converts a failure into a reusable textual lesson ("I under-inferred save/persistence features on document-type apps") stored in a memory the next inference reads

This is a deployable middle layer between one-shot prompting and expensive fine-tuning — cheap enough to run at inference time, principled enough to actually improve over trials. It needs only an LLM API, a memory store, and an evaluation function.

### 7. The Critical Fix: Don't Let It Reflect Alone
**The single most important finding for this subsystem**: a single agent reflecting on its own failures **gets stuck in local optima** — it reinforces its own existing assumptions, a documented failure mode called *"degeneration of thought."*

The fix is **Multi-Agent Reflexion**: multiple critics with different personas reviewing the same output. Research assigns roles like:
- **Skeptic** — questions the assumptions behind each inferred requirement
- **Logician** — checks strict correctness and consistency
- **Creative Thinker** — suggests alternatives and things nobody proposed

Multi-Agent Reflexion consistently outperforms single-agent Reflexion on benchmarks (HotPotQA, HumanEval). This maps perfectly onto MAP's existing multi-agent shape and the shared-workspace principle: **emergence's self-review must be a crew of differently-angled critics, not one agent grading its own homework.** This is the highest-leverage single improvement in this document.

### 8. End-of-Day: Experiential Memory (ExpeL-style)
For batch self-improvement, the pattern is **comparing successful vs. failed trajectories to extract reusable insights** (ExpeL, Zhao et al., 2024). Rather than reflecting on one task in the moment, batch-analyze the day's runs:
- What did emergence miss across *all* of today's tasks?
- What patterns recur in the misses (e.g., "consistently under-infers error-handling requirements")?
- Distill those into heuristics stored for tomorrow.

The research explicitly notes this is the **most deployable** form of self-improvement ("self-improvement 1.0") — no special infrastructure, just accumulated experience compared across trajectories. It's the natural "at the end of the day" mechanism you asked for, and it complements (doesn't replace) the real-time Reflexion loop.

### 9. Three Cautions From the 2026 Literature
1. **Make the evaluator explicit and stable.** Reproducibility reviews stress that Evaluator output must be consistent across retries — "avoid reward jitter." A noisy quality signal means the loop learns noise. Ground it in something machine-checkable wherever possible.
2. **Beware the critic that "fixes" what was already right.** A documented single-shot-critique failure: the critic rewrites a correct output with extra hedging, dropping specificity without improving anything. The loop must be allowed to conclude "this was fine, leave it" rather than feeling obligated to change something every pass.
3. **Run reflection on a subset, not everything.** Reflection multiplies token cost per round, so production systems sample rather than reflecting on all traffic. For a home/local-model setup this matters: reserve deep multi-critic reflection for high-gap tasks (Section 1's gap score decides), and let low-gap tasks pass through cheaply.

---

## PART THREE — How It Fits MAP

### 10. Connection to the Rest of the System
- **Cybernetic grounding** (Wiener, Philosophical Foundations): the inward loop is literally a cybernetic feedback loop — the system observing the gap between intended and actual behavior and correcting it.
- **Self-auditing target** (Requirements Outline, Section IV.C): this subsystem is how MAP moves from manual periodic audit to continuous self-diagnosis, for the emergence subsystem specifically.
- **Threshold-gated action** (Principle 2, Cross-Domain research): both halves use confidence thresholds — auto-add only above threshold (outward), and act on a reflection only when the evaluator signal is strong and stable (inward).
- **Shared state over messaging** (Principle 1): both the inference crew and the critic crew operate over a shared workspace, not message-passing.

### 11. Suggested Build Order
1. **Gap score first** (Section 1) — cheap, and it gates the cost of everything else.
2. **Two-pass inference** (Section 2) — the core outward capability.
3. **Reflexion loop with a stable evaluator** (Section 6 + Caution 1) — the minimum viable inward loop.
4. **Multi-critic reflection** (Section 7) — the highest-leverage upgrade; add the Skeptic/Logician/Creative-Thinker crew once the basic loop works.
5. **End-of-day experiential memory** (Section 8) — batch consolidation, added last because it depends on having accumulated trajectory data to compare.

### 12. The One-Sentence Summary
Emergence infers what a task should have said; turned inward, it infers what its own inference process keeps getting wrong — and the key to both is never letting a single agent be the sole judge of its own output.

---

*Companion document to the MAP series. Directly extends MAP-System-Requirements-Outline.md (self-auditing target) and MAP-Cross-Domain-Research-III.md (threshold-gated response). Governed by the two design principles in MAP-Index.md.*
