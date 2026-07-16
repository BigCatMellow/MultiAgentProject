# MAP Sensitivity / Robustness-Grading Method (TASK-149, Wave 2)

Status: draft-active
Owner: command-center
Built by: TASK-149

## Purpose

Round 6 of the 6.13 simulation series (`sensitivity.py`,
`Guidelines/6.13/files8/MAP-Simulation-Results-Round6.md`) graded which of
the design's load-bearing conclusions are robust across the full plausible
parameter space vs. conditional on specific, unmeasured real-repo numbers.
The master implementation plan's nine waves did not include this as an
ongoing practice — this document defines one, so future validator/library/
policy decisions get graded the same way rather than trusted or dismissed by
assertion.

## The Method (ported from Round 6)

1. **Identify the conclusion** — a specific, falsifiable claim a design
   decision rests on (e.g. "eager halt beats threshold gating", "the
   Library layer beats no-library").
2. **Name the underlying parameters** the conclusion depends on (cost
   ratios, defect rates, false-positive rates, compression ratios, churn
   rates, misattribution rates).
3. **Define the plausible range** for each parameter — not a single assumed
   value, but a defensible min/max informed by whatever real data exists
   (or, absent real data, a wide range that brackets plausible reality).
4. **Sweep the space** — vary each parameter (or combinations) across its
   range and re-check whether the conclusion still holds.
5. **Report the fraction of the space where it holds** as the grade.
6. **Classify**:
   - **Robust** (~90%+ of plausible space): safe to build on directly.
   - **Conditional** (~60-85%): flag exactly which real parameter(s)
     decide it, and what threshold flips it — this is the valuable output,
     because it converts vague uncertainty into a specific measurement
     target (see `map-real-parameter-calibration.md`).
   - **Unsupported** (<~50%, or majority-negative): treat as a hypothesis,
     not a conclusion; do not build production behavior on it without
     first narrowing the parameter range with real data.

## Existing Grades (carried over from Round 6, for reference — not re-derived here)

| Conclusion | Grade | Class |
|---|---|---|
| C1 — Eager halt beats threshold gating | 92% | Robust |
| C2 — Knowledge layer (full) beats no-library | 69% | Conditional (compression ratio, churn rate) |
| C3 — Idempotency prevents silent corruption | 94% | Robust |
| C4 — Emergence needs a pruning guard | 75% | Conditional (misattribution rate) |

These four are inherited findings, not re-verified in this task. New
conclusions this method should be applied to going forward (not yet graded,
flagged here as candidates):

- The ~1% false-positive target for the eager-halt policy (Gap-Register
  2a / Round-files7 finding: FP rate stayed flat ~8.2% regardless of L1
  deterministic coverage — this itself needs a robustness grade once the
  L2 fuzzy judge is built and real accuracy data exists, not just the
  simulated one).
- Wave 3's cost-governance thresholds (per-task/per-day budget caps) once
  real spend data exists.
- Wave 8's pre-dispatch policy checker's false-reject rate, once built.

## When To Apply This

Apply the grading method (not necessarily the full sweep-across-space
rigor, which needs a harness like `sensitivity.py`) at these points:

- Before treating any Wave 3-9 threshold, cost ratio, or accuracy target as
  settled rather than provisional.
- After each real-parameter measurement batch (see
  `map-real-parameter-calibration.md`'s recommended follow-on task) —
  re-check whether newly measured real data moves a Conditional conclusion
  toward Robust or toward Unsupported.
- Before removing a safeguard (e.g. relaxing the eager-halt policy, or
  disabling a resilience mechanism) — Round 4 found each resilience
  mechanism independently load-bearing for a distinct failure mode; do not
  remove one because a different failure mode wasn't observed recently.

## Difference From One-Time Calibration

`map-real-parameter-calibration.md` measures what the real numbers *are*.
This method grades how much a conclusion's *validity* depends on getting
those numbers right — the calibration feeds this method's parameter ranges,
but this method is the reusable practice for deciding which future
conclusions need calibration before they're trusted, not a one-time report.

## Related Files

- `Guidelines/6.13/files8/MAP-Simulation-Results-Round6.md`
- `Guidelines/6.13/files8/sensitivity.py`
- `MAP_System/artifacts/audits/map-real-parameter-calibration.md` [[map-real-parameter-calibration]]
- `MAP_System/artifacts/planning/map-613-master-implementation-plan.md` [[map-613-master-implementation-plan]] (Wave 9)
