# MAP Validator Specification
### Turning the Biggest Black Box Into a Real (and Honestly Bounded) Design

The validator is the single most load-bearing assumed component in MAP: the entire eager-halt conclusion — the biggest correction from the simulation rounds — rests on "the validator catches defects at ~1% false positives." Every round assumed this. None specified how. This document specifies it, and reports what a direct test revealed: **the architecture achieves high catch cheaply, but the ~1% false-positive target is not something the architecture delivers — it depends on the hard, still-unsolved accuracy of the fuzzy judge.** The honest version matters more than the clean one.

Evidence from `validator_design.py`, 8 seeds.

---

## The Design: A Layered Cascade

The validator is two layers, cheapest first:

**Layer 1 — Deterministic checks.** Everything mechanically verifiable, run on every output:
- Schema/structure (does it match the MATOCP shape?)
- Type checks, parse checks (does the code/JSON/config still parse?)
- Tests (does the existing test suite still pass?)
- Invariants (task IDs unique, counts non-negative, no orphan references, canonical state still well-formed)

These are **ground truth**: a failing test or a schema violation is a real defect, not a guess. Layer 1's false-positive rate is near zero because it only flags things that are provably wrong.

**Layer 2 — Fuzzy judge.** An LLM-as-judge (or equivalent) that inspects outputs for **semantic** defects — well-formed, schema-valid output that is nonetheless *logically wrong* (the em-dash miscount from the test-drive, a plausible-but-incorrect calculation). This is the layer that catches what determinism can't. It is also the **only meaningful source of false positives**, because it operates on judgment, not proof.

---

## What the Test Confirmed

**Catch rate scales strongly with deterministic coverage.** As the fraction of defects Layer 1 can mechanically catch rises from 0% to 95%, overall catch climbs from 75% to 98.7%. Investing in more deterministic checks (more tests, more invariants, more property checks) is real, high-value work — it directly raises how many defects are caught with certainty.

---

## What the Test *Corrected* (the important part)

The design was built around a claim that turned out to be **wrong**: that raising deterministic coverage would drive the false-positive rate down. It does not.

- **False-positive rate stayed flat at ~8.2% regardless of deterministic coverage** (0% → 95%).
- The reason, obvious in hindsight: deterministic checks catch *defects*, but false positives come from Layer 2 firing on *clean* outputs — and every clean output still reaches Layer 2 no matter how good Layer 1 is. Better deterministic coverage does nothing to stop the fuzzy judge from false-flagging correct work.

**The actual lever is Layer 2's own accuracy.** The test showed overall false-positive rate tracks the judge's intrinsic false-positive rate almost exactly: an 8% judge yields ~8% overall; a 1% judge yields ~1.2% overall. So hitting the ~1% target the whole system assumes depends entirely on building a fuzzy judge that is itself accurate to ~1% — which the cascade architecture does **not** provide for free.

**The honest bottom line:** the recommended design (high deterministic coverage + a moderately disciplined judge at 4% false positives) achieves **96% catch but 4.4% false positives — over 4× the assumed target.** The layered architecture is genuinely good for catch and for cost (deterministic checks are cheap), but the ~1% false-positive assumption requires solving judge accuracy separately, and that is hard and unsolved.

---

## How to Actually Attack Judge Accuracy (the residual hard problem)

Since the architecture doesn't deliver ~1% on its own, these are the levers that must, and none is free:

- **Require a cited, checkable reason.** The judge must not flag "this seems wrong" — it must point to a specific claim that can be re-checked (ideally handed *back* to Layer 1 to verify). A judge forced to justify itself against a verifiable criterion false-flags far less. This is the highest-value single discipline.
- **Ensemble / multi-judge for high-severity only.** Round 3 showed universal redundancy is net-negative, so reserve multiple independent judges for high-severity outputs (where a shipped defect is expensive), and accept a single judge elsewhere.
- **Calibrate the flag threshold against labeled data.** The judge's confidence-to-flag cutoff should be tuned against a real set of known-good and known-bad outputs, not set by intuition — this is the direct analog of the ~1% false-positive target being a *measured*, not assumed, number.
- **Feed false positives back as training/calibration signal.** Every false halt the operator overrides is a labeled example; the judge (or its threshold) should learn from them — closing the loop, and directly mitigating the trust-erosion dynamic from Round 2.

**Maximize deterministic coverage anyway** — not because it lowers false positives (it doesn't), but because every defect Layer 1 catches with certainty is one that never reaches the fallible judge, raising overall catch and reducing how much the expensive judge is even invoked (~74% of traffic still hit it at 85% coverage, so there's a cost argument too).

---

## Connection to the Rest of MAP

- **The eager-halt policy (the biggest simulation correction) is now conditional on this.** "Halt eagerly but be accurate" is only safe if judge accuracy is actually solved. Until the real judge's false-positive rate is *measured* (Gap Register 2a → 3.1), eager halting is a hypothesis, not a settled result. This spec makes that dependency explicit rather than hidden.
- **Layer 1 is where the deterministic power of `validate_task_graph.py` already lives** — the existing invariant checker is the seed of Layer 1; the work is expanding its coverage.
- **The feedback loop ties to emergence and observability** — overridden false halts are labeled data (emergence-style learning), and every halt is a traced event (observability).

---

## Honest Status

The validator is no longer a total black box — its architecture is specified and its catch behavior is tested. But its hardest sub-problem (a fuzzy judge accurate to ~1% false positives) is **specified as a problem, not solved**, and the test proved the architecture alone won't reach the assumed target. This is progress and a sharpened open question, not a closed one. The single most important real-world action remains: **measure the actual judge's false-positive rate on real outputs**, because every downstream conclusion about eager halting depends on that number being genuinely low — and the simulation just showed it won't be low by default.

---

*Companion to MAP-The-Synthesized-System.md and MAP-Gap-Register.md (item 2a). Harness: validator_design.py. Corrects an initial design assumption via test — the layered cascade solves catch and cost, not false positives.*
