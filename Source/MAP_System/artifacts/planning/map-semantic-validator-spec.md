# MAP Semantic Validator Spec (TASK-152, Wave 4)

Status: draft-active
Owner: command-center
Built by: TASK-152
Companion: `map-protocol-validator-spec.md`, `map-validator-halt-state-spec.md`
Source: `Guidelines/6.13/files7/MAP-Validator-Specification.md` (Gap-Register 2a)

## Purpose

Specifies the general output-correctness validator — the harder of the two
black boxes the 6.13 corpus identifies (Gap-Register 2a), distinct from the
protocol/MATOCP validator (`map-protocol-validator-spec.md`). This is "does
the work actually do the right thing," not "was the message shaped right."

## Design: Layered Cascade (ported from `MAP-Validator-Specification.md`)

**Layer 1 — Deterministic checks**, run on every output, near-zero false
positives because they only flag provably wrong things:

- Schema/structure validity.
- Parse/type checks (does code/JSON/config still parse?).
- Existing test suite still passes.
- Invariant checks: task ID uniqueness, non-negative counts, no orphan
  references, canonical state well-formed.
- **MAP-specific L1 checks that already exist and should be treated as this
  layer's current implementation**: `scripts/validate_task_mirrors.py`,
  `scripts/validate_task_graph.py`, `scripts/validate_events.py`,
  `scripts/validate_shared_state.py`, `scripts/validate_decisions.py`,
  `scripts/validate_review.py`. Building this validator is substantially
  "wire these together as one Layer 1," not building from scratch.

**Layer 2 — Fuzzy judge**, an LLM-as-judge for semantic defects that are
schema-valid but logically wrong (a plausible-but-incorrect calculation, a
subtly wrong acceptance-criteria interpretation). This is the only
meaningful source of false positives.

## Critical Finding This Spec Must State Explicitly (acceptance criterion #2)

**Layer 1 coverage improves catch rate; it does NOT reduce Layer 2 false
positives.** Per the simulation test (`validator_design.py`, 8 seeds):

- Catch rate scales strongly with L1 coverage: 75% → 98.7% as deterministic
  coverage rises 0% → 95%.
- False-positive rate stays **flat at ~8.2%** regardless of L1 coverage
  (0% → 95%) — because L1 catches defects, but false positives come from L2
  firing on *clean* outputs, and every clean output still reaches L2 no
  matter how good L1 is.
- Overall false-positive rate tracks L2's own intrinsic false-positive rate
  almost exactly (an 8% judge yields ~8% overall; a 1% judge yields ~1.2%).

**Implication for MAP**: do not treat "add more deterministic rules/tests" as
a path to the ~1% false-positive target the eager-halt policy assumes. That
target is a **judge-accuracy problem**, separate from L1 investment. L1
investment is still valuable (raises catch, lowers cost by keeping more
traffic out of the expensive judge) — just not for false-positive reduction.

## Judge-Accuracy Levers (the actual open problem, not solved by this spec)

Per `MAP-Validator-Specification.md`, in priority order:

1. **Require a cited, checkable reason.** The judge must point to a specific
   claim re-checkable by Layer 1, not "this seems wrong." Highest-value
   single discipline.
2. **Reserve multi-judge ensembles for high-severity outputs only** —
   universal peer review was cut as net-negative by simulation (Round 1,
   Round 3); redundancy pays only where a shipped defect is expensive.
3. **Calibrate the flag threshold against labeled real data**, not
   intuition — mirrors the real-parameter-calibration discipline from
   TASK-149.
4. **Feed overridden false positives back as calibration signal** — closes
   the loop with the halt-state's adjudication tracking
   (`map-validator-halt-state-spec.md`) and with Emergence's learning loop.

None of these four are built by this task. This spec names them as the
required follow-on work; TASK-152's deliverable is the specification and
halt-state design, not the judge implementation itself.

## Relationship To The Protocol Validator

The two validators are independent and must not be conflated (this was
exactly TASK-147's review finding): a message can be protocol-compliant and
semantically wrong (well-formed `!FIX` describing an incorrect fix), or
protocol-noncompliant and semantically correct (correct fix described in
plain prose without the token form). Both validators run; neither implies
the other's result.

## Relationship To Self-Repair

A validator-caught defect maps onto `SELF_REPAIR_SYSTEM.md`'s severity
ladder:

- L1 catch (schema/invariant violation) → typically `DRIFT` or `BLOCKING`,
  mechanical to fix.
- L2 catch (semantic defect) → typically `BLOCKING`, requires judgment —
  escalate per Self-Repair's existing rule (Repair Record + `--intent
  request` before acting).
- A false-positive override → not a repair at all; it's calibration data
  for the judge (see Judge-Accuracy Levers above), logged as such, not
  filed as a Repair Record.

## Non-Goals For This Task

- Does not build or select the actual LLM-judge implementation.
- Does not measure the real judge's false-positive rate (that is
  `map-real-parameter-calibration.md`'s parameter #4, blocked on this
  validator existing first — a genuine sequencing dependency: you cannot
  measure judge FP rate before the judge exists to be measured).

## Related Files

- `Guidelines/6.13/files7/MAP-Validator-Specification.md`
- `Guidelines/6.13/MAP-Gap-Register.md` (item 2a)
- `MAP_System/artifacts/planning/map-protocol-validator-spec.md` [[map-protocol-validator-spec]]
- `MAP_System/artifacts/planning/map-validator-halt-state-spec.md` [[map-validator-halt-state-spec]]
- `MAP_System/artifacts/audits/map-real-parameter-calibration.md` [[map-real-parameter-calibration]]
- `MAP_System/SELF_REPAIR_SYSTEM.md` [[SELF_REPAIR_SYSTEM]]
