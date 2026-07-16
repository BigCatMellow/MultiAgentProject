# Running the MAP Simulation Harness

Four progressive versions, each runnable standalone with `python3 <file>`:

- `map_v1.py` — baseline MAP exactly as the design docs specify. Run it to see the starting numbers (47% catch, 83 interrupts).
- `diagnose_v1.py` — breaks down WHERE defects escape and WHY interrupts are high.
- `map_v2.py` — threshold sweep + validator architecture bake-off. Shows threshold=1 wins.
- `map_v3.py` — adds a cost model; tests source-side defect levers. Shows strict-routing and pre-tokenization are net-negative.
- `map_v4.py` — realistic peer-review modeling + robustness stress tests. Shows the final tuned config holds 100% catch under 2x load + degraded agents.

No dependencies beyond the Python standard library. Each is seeded, so results are reproducible.

## To adapt to your real system
The two parameters that drove every decision are at the top of `map_v3.py`:
```
COST_SHIPPED_DEFECT = 8.0   # measure your real value
COST_FALSE_HALT     = 1.5   # measure your real value
```
and agent skill in each `build()`:
```
Agent("Cloud-1","cloud",skill=0.85,...)   # measure real defect rates
Agent("Local-1","local",skill=0.75,...)
```
Re-run after plugging in your measured numbers. If your cost ratio differs sharply from 8:1, re-check the threshold decision.
