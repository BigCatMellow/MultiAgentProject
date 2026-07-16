# MAP Robustness Grading — First Report (2026-07-14)

- Task: TASK-188
- Owner: claude-lab-toku
- Method: `map-sensitivity-robustness-method.md` [[map-sensitivity-robustness-method]] (Round-6 port)
- Inputs: `map-real-parameter-calibration-results-2026-07-14.md` [[map-real-parameter-calibration-results-2026-07-14]] (this task's measurement batch)
- Scope note: the method's full sweep-across-parameter-space rigor needs a
  harness like `sensitivity.py`; per the method's own "When To Apply This"
  section, this report applies the grading judgment using real measured data
  to move each inherited grade, not a re-simulation. Where real data cannot
  move a grade, that is said outright.

## Grades

| Conclusion | Round-6 grade | This report | Deciding evidence |
|---|---|---|---|
| C1 — Eager halt beats threshold gating | Robust (92%) | **Robust (unchanged, still unexercised in reality)** | Zero real halts ever; defect side of the cost ratio now real (3 shipped defects, minutes-scale fixes) |
| C2 — Knowledge/Library layer (full) beats no-library | Conditional (69%) | **Conditional — currently NEGATIVE for this corpus** | Compression condition met (22.65x floor); churn condition failed (low steady-state churn) |
| C3 — Idempotency/atomicity prevents silent corruption | Robust (94%) | **Robust — now with real-repo confirmation** | Real ID collisions reproduced unlocked (3/8), zero after lock; mirror-drift caught by gate |
| C4 — Emergence needs a pruning guard | Conditional (75%) | **Unsupported at current scale** | Measured misattribution 0/15, far below the 20% build threshold |
| V — ~1% false-positive target achievable for L2 semantic validation | (flagged, ungraded) | **Unsupported** | No L2 judge exists; zero adjudicated telemetry; only contrary evidence is simulated (FP flat ~8.2%) |
| R — Universal peer review is net-negative (Rounds 1/3 cut) | (cut applied) | **Unsupported by real data — flagged for reversal review** | Real review-catch rate 23.1% (36/156), all recovered pre-release |
| P1 — Coordination via shared state, not messages | Validated (Round 1) | **Robust in mechanism, Conditional in practice** | All lifecycle gates enforce shared state; but agent messages outnumber durable writes 2.35:1 |

## C1 — Eager halt beats threshold gating: ROBUST (unchanged), with a caveat the grade cannot capture

The inherited 92% grade stands because no real data contradicts it — but no
real data exercises it either. The real repo has **never set a halt**
(validators ship telemetry-only; `halt-state.json` untouched since creation).

What real data did move: the cost ratio's defect side is no longer assumed.
Three real shipped defects cost minutes-scale fixes (1.9–14 min recorded
spans, discovery cost excluded). Zero false halts have occurred — trivially,
since zero halts have occurred. Direction of the sparse evidence is
consistent with eager halting (real defects exist; false halts remain
hypothetical), but the deciding parameter (8:1 shipped-defect:false-halt cost)
is still unmeasured.

**What flips it / next measurement:** run `validate_layer1.py` with halt
authority enabled for a bounded window (or keep telemetry-only but adjudicate
every violation), then compute the real ratio. Until then, do not treat the
92% as verified — treat it as unfalsified.

## C2 — Library layer pays off only in full: CONDITIONAL, currently negative for this corpus

Round 6 said the conclusion holds in 69% of parameter space, deciding
parameters compression ratio and churn. Both are now measured:

- Compression: 22.65x median extractive floor — clears the ~2x threshold by
  an order of magnitude, but TASK-174's caveat is load-bearing: it is a floor
  with an almost-certainly-high detail-needed rate, which is the other half
  of the adoption test and remains unmeasured.
- Churn: **low** in steady state (4-5 shared/system write-events in the
  current week, vs 107 during the build sprint), concentrated in 2-3 files.

Per Round 6's own rule (pays off only when compression is high **AND** churn
is not low), the measured parameters land this corpus in the "do not build
yet" region. This independently confirms TASK-174's verdict by a different
route (TASK-174 argued from detail-needed risk; this grading arrives via
churn).

**What flips it:** sustained (not sprint-burst) churn growth, plus a measured
detail-needed rate from TASK-174's recommended 3-5-doc pilot.

## C3 — Idempotency/atomicity prevents silent corruption: ROBUST, now real-confirmed

The only conclusion where real repo history supplies direct confirmation on
both sides:

- Without the mechanism: TASK-141 reproduced real emergence ID collisions
  under 8-way concurrency (3/8 collisions; REPAIR-0005), and two agents
  really did file colliding `REPAIR-0001` records before that (found in
  TASK-129). Simulation Round 2's 599/600 unlocked-collision finding has a
  real-world miniature.
- With the mechanism: zero collisions since the per-kind flock landed; zero
  task-ID collisions since `--task-id auto`; mirror drift is caught by
  `validate_task_mirrors.py` at gate time (drift that TASK-140/141 previously
  found manually).

Keep the 94%→Robust grade; this is now the best-evidenced conclusion in the
set. Per the method's safeguard rule: do not remove any of these locks based
on recent quiet — the quiet is the mechanism working.

## C4 — Emergence needs a pruning guard: UNSUPPORTED at current scale

Round 6 graded this Conditional (75%) on the misattribution rate, threshold
~20%. Measured: **0/15 promoted records misattributed** (see calibration
results §3 for method and the 3 lifecycle-noise records that are ceremony
errors, not misattribution).

At 0% observed vs a 20% threshold, the conclusion "MAP needs to build the
pruning guard now" is unsupported for the current corpus. Grade honestly
qualified: N=15, manual adjudication, no automated outcome tracking, young
records. This is "don't build yet," not "never build."

**What flips it:** emergence volume growth (N≥50 promoted records), or
outcome-feedback implementation revealing misattributions the manual read
missed. Re-grade after either.

## V — The ~1% L2 false-positive target: UNSUPPORTED

Called out by the method doc itself as a grading candidate. Real state: no L2
fuzzy judge exists; `validate_protocol.py` ships severity-capped at DRIFT
with an adjudication field that has never accumulated data; the only accuracy
evidence anywhere is simulated (files7: FP stayed ~8.2% regardless of L1
coverage — i.e. against the target). An unbuilt component with only contrary
simulated evidence cannot carry a production dependency: any design that
assumes the 1% target (including full eager-halt-on-L2) should treat it as a
hypothesis. The current telemetry-only shipping posture is exactly right for
this grade.

## R — "Universal peer review is net-negative" (the Rounds 1/3 cut): UNSUPPORTED BY REAL DATA — flagged

This is the one place real data pushes **against** an applied simulation
conclusion, so it is flagged prominently rather than buried: the simulations
cut strict routing and universal peer review as net-negative *once the
validator already catches defects*. But in the real repo, the premise is
absent — the semantic validator does not exist and L1 runs telemetry-only —
while review is doing exactly the work the simulation assigned to the
validator: **23.1% of submissions (36/156) drew CHANGES_REQUESTED, and all 36
were fixed pre-release.** The three defects that did ship (TASK-050/177/179
fixes) got past review, not past a validator.

The simulation cut was conditional on a validator that reality doesn't have
yet. Until L2 exists and its catch rate is measured, MAP's mandatory review
gate is carrying the defect-catch load and should not be weakened on
simulation grounds. (This does not conclude review would stay net-positive
*after* a real validator lands — that is precisely the re-grading trigger.)

## P1 — Shared-state coordination: ROBUST in mechanism, CONDITIONAL in practice

Mechanism: every lifecycle-critical transition (claim, promote, approve,
release, halt) is enforced through directly-readable shared state with gate
scripts — no relay chain can bypass it. That part of Principle 1 is built-in
and graded Robust.

Practice: agents still exchange 2.35 messages per durable state write
(2,524 vs 1,074 over the full window). Much of that is legitimately social
(review threads, acks, routing), and the intent split needed to say how much
is coordination-that-should-be-state is not recorded consistently — so the
practice half stays Conditional with a named missing measurement (hcom intent
classification), rather than being guessed.

## Standing Re-Grade Triggers (per the method's "When To Apply This")

1. After outcome feedback ships → re-grade C4 (automated misattribution) and
   start the validator blind-spot series (feeds V and R).
2. After any bounded halt-authority window → re-grade C1 with a real cost
   ratio and V with real FP data.
3. After the Library pilot (if the operator approves it) → re-grade C2 with a
   real detail-needed rate.
4. After L2 semantic validator lands and accumulates adjudications → re-grade
   R (review-cut reversal question) — do not weaken the review gate before
   this trigger fires.

## Related Files

- `map-sensitivity-robustness-method.md` [[map-sensitivity-robustness-method]]
- `map-real-parameter-calibration-results-2026-07-14.md` — the measurement batch behind every grade above
- `map-real-parameter-calibration.md` [[map-real-parameter-calibration]]
- `Guidelines/6.13/files8/MAP-Simulation-Results-Round6.md` — inherited grades' origin
- `source-mining-audit-2026-07-14.md` — ranked this work #1
