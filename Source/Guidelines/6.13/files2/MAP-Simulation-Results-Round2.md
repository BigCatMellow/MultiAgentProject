# MAP Simulation Results, Round 2: Deeper Testing
### Concurrency Relocated, Trust Erosion Found, and the Threshold Question Finally Resolved

This is the second round of simulation, pushing on the caveats the first round left standing. It produced three findings that materially change the recommendations — including one that corrects an engineering requirement the first round got subtly wrong, and one subtle result that reframes the central threshold decision. It also includes two of my own broken tests, reported honestly because a test that returns false confidence is worse than no test.

All results from `map_v5.py` through `map_v7.py`, 8–10 seeds each.

---

## Finding 1: The cost-ratio caveat is retired — threshold=1 is more robust than claimed

Round 1 flagged that the threshold=1 decision might flip if false halts were expensive. Round 2 swept the full cost range to find the flip point. **There is no flip point in any realistic range.** Threshold=1 wins even when a false halt costs **30 — nearly 4× a shipped defect**:

| False-halt cost | Ratio (ship:false) | thr=1 cost | thr=2 cost | Winner |
|---|---|---|---|---|
| 1.5 | 5.33 | 733 | 1019 | thr=1 |
| 8 | 1.00 | 838 | 1073 | thr=1 |
| 16 | 0.50 | 967 | 1140 | thr=1 |
| 30 | 0.27 | 1192 | 1258 | thr=1 |

The caveat can be retired: on pure cost, halt-eagerly wins across the board.

---

## Finding 2 (the important correction): The real concurrency risk is cross-PROCESS, not threads

Round 1 "validated" the atomic allocator in a sequential simulation — a weak test. Round 2 tried to test it under real concurrency and, in the process, uncovered something that changes the engineering requirement.

**First, an honest failure:** two successive attempts to reproduce the race with Python *threads* returned false "SAFE" results. The reason turned out to be substantive, not incidental: **Python's GIL serializes bytecode, so the classic read-modify-write race is nearly impossible to trigger with threads.** Reporting "SAFE" from those tests would have been exactly the false confidence this whole exercise exists to prevent.

**Modeled at the level the bug actually occurs — separate processes sharing a task-ID file — the result is stark:**

| Variant | Allocations | Unique IDs | Collisions | Verdict |
|---|---|---|---|---|
| Unlocked (processes) | 600 | 1 | **599** | FAILS |
| File-locked | 600 | 600 | 0 | SAFE |

Nearly every allocation collides when unlocked: each process reads the same max ID, each computes max+1, each writes the same value. This is the near-deletion mechanism, reproduced.

**The corrected requirement:** MAP's real risk was never thread-level. It is **cross-process** — separate agent processes touching the same git repo and task files with no shared lock. Therefore `map-git` must enforce a genuine **cross-process lock** (an OS-level file lock or equivalent), not merely wrap git and not merely use an in-process lock. An in-process thread lock would pass every test and still let the incident happen in production. *This is a sharper, more correct version of the Phase-0 requirement than Round 1 produced.*

---

## Finding 3 (the subtle one): Threshold=1 erodes trust — but the fix is accuracy, not a higher threshold

This is the most nuanced result of the entire simulation, and it reopens then re-closes the central question.

**The problem.** Round 1's cost model treated a false halt as just a fixed cost. But the Lessons-Learned document warned (via the Artificial Immune Systems literature) that a noisy validator gets *ignored* — operators stop trusting it and override it. Round 2 modeled that: operator trust decays with each false halt, and below a trust threshold the operator starts overriding halts, letting real defects through.

Under this model, over a 10-day horizon, **threshold=1's higher false-halt count craters trust and its real catch rate falls from 100% to ~79%.** Threshold=2 preserves more trust. For a moment, this looked like vindication of the design docs' threshold gating.

**The resolution.** But raising the threshold is the wrong lever — it buys trust by *sacrificing catch rate* (threshold=2 catches only 47%). The right lever is validator **accuracy**. Holding threshold=1 and driving the false-positive rate down:

| Validator FP rate | False halts (10 days) | Final trust | Defects shipped | Real catch rate |
|---|---|---|---|---|
| 5.0% | 34.8 | 0.07 | 45.2 | 79.3% |
| 2.5% | 17.9 | 0.46 | 2.6 | 98.6% |
| **1.2%** | 8.8 | 0.74 | 0.0 | **100.0%** |
| 0.5% | 3.3 | 0.90 | 0.0 | 100.0% |

At a ~1% false-positive rate, threshold=1 delivers **100% catch, preserved trust (0.74), and zero shipped defects** — beating threshold=2's 47% catch on every axis simultaneously.

**The corrected principle, stated precisely:**
> **Halt eagerly (threshold=1), but be accurate (keep false positives near ~1%).**

The design docs' instinct to raise the threshold was trying to solve trust erosion with the wrong tool — trading away defect-catching to reduce false alarms. The simulation shows the two goals aren't in tension *if* you attack the false-positive rate directly. Threshold gating was a workaround for an inaccurate validator; fix the accuracy and the workaround becomes unnecessary and harmful.

---

## Updated Tuned Configuration (corrections from Round 2 in bold)

```
STATE
  Atomic task-ID allocation via a **cross-PROCESS lock** (OS file lock),
    NOT a thread lock and NOT a bare git wrapper.        [CORRECTED]
  Mutual-exclusion write lock, same cross-process requirement.

VALIDATION
  Halt on first raised signal (threshold=1).             [confirmed, robust to 4x cost]
  **Invest in validator ACCURACY: drive false-positive rate to ~1%.**  [NEW — this is
    the lever that was missing; it's what makes eager halting safe long-term]
  Track operator-trust proxy (false-halt rate over time); if false halts
    climb, fix accuracy rather than dulling the validator. [NEW]

(everything else unchanged from Round 1's tuned config: single entry point,
 shared-state coordination, basic cognitive-load routing, emergence with
 recalibrated confidence, end-of-day learning, structured logging;
 threshold gating, strict routing, pre-tokenization, and peer review remain CUT.)
```

---

## Two Tests I Got Wrong (reported deliberately)

1. **Thread-based race test (v5, v6):** returned false "SAFE" because the GIL prevents bytecode races. Fixed in v7 by modeling at process level. *Lesson: test a failure mode at the level it actually occurs, or the test lies.*
2. **Typo crash (v6):** referenced a non-existent validator attribute. Trivial, fixed in v7. *Lesson: even in throwaway experiment code, a crash is cheaper than a silently wrong number.*

Both are included because the entire premise of this exercise is that measured results beat plausible assumptions — which only holds if the measurements are honest, including about their own failures.

---

## Where This Leaves the Real Backlog

The two highest-value, now-sharpened actions for the real repo:

1. **Verify `map-git` holds a cross-process lock.** Not a thread lock, not just a git wrapper — an OS-level file lock (e.g. `flock`) around the read-compute-write of task-ID allocation and canonical writes. Test it by launching two real agent processes that both allocate simultaneously and checking for collisions. This is the direct near-deletion fix.
2. **Measure and then minimize the validator's false-positive rate.** The whole long-term-viability case for eager halting rests on keeping false positives near ~1%. Instrument the real validator to log false positives, and treat that rate as a first-class metric — because if it drifts up, trust erodes and the eager-halt policy silently degrades.

---

*Round-2 companion to MAP-Simulation-Results.md. Corrects the Phase-0 concurrency requirement and resolves the threshold question via validator accuracy. Harness: map_v5.py–map_v7.py.*
