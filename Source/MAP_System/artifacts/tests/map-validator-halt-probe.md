# MAP Validator Halt Probe (TASK-152, Wave 4)

Task: TASK-152
Owner: command-center
Companion: `map-validator-halt-state-spec.md`

## Purpose

Demonstrates that a validator can actually halt dispatch, not only log —
the direct acceptance test for this task's 4th criterion, and a follow-on
to `map-613-simulation-testdrive-probes.md`'s Probe 2, which found
structural/mirror validators already halt (via `map_task.py approve`
refusing on drift) but the general protocol/semantic validator described in
this task's other three specs does not exist yet.

## What This Probe Can Demonstrate Today (structural halt, already built)

```bash
# Deliberately introduce mirror drift in a disposable copy, never canonical state
cp MAP_System/map.db /tmp/halt-probe-map.db
cp MAP_System/workflow/task_graph.json /tmp/halt-probe-task-graph.json
python3 -c "
import sqlite3
conn = sqlite3.connect('/tmp/halt-probe-map.db')
conn.execute(\"UPDATE tasks SET status='APPROVED' WHERE task_id=(SELECT task_id FROM tasks LIMIT 1)\")
conn.commit()
"
# task_graph.json mirror now disagrees with the doctored DB copy
python3 MAP_System/scripts/validate_task_mirrors.py --db /tmp/halt-probe-map.db --task-graph /tmp/halt-probe-task-graph.json 2>&1 || echo "exit=$?"
```

**Pass condition:** non-zero exit, explicit mismatch message — this is a
real halt (the command that would gate `approve`/`release` refuses), not a
silent log line. (Note: `validate_task_mirrors.py` may not currently accept
`--db`/`--task-graph` overrides; if not, run this against a full disposable
repo copy instead — the point is to prove the check blocks on a real
fixture, never to run a corruption test against canonical `map.db`.)

## What This Probe Cannot Yet Demonstrate (the actual Wave 4 gap)

There is no probe for the protocol validator or semantic validator halting,
because neither exists yet as running code — only as the specs this task
delivers (`map-protocol-validator-spec.md`, `map-semantic-validator-spec.md`,
`map-validator-halt-state-spec.md`). This is the honest state, matching
`map-613-simulation-testdrive-probes.md`'s finding: "Probe 2 ... Partially
confirmed ... The semantic/protocol validator from Wave 4 does not exist
yet."

## Probe Design For The Future Implementation Task (not built here)

Once the kill-switch halt store (`map-kill-switch-spec.md`, TASK-151) and
the protocol/semantic validators exist, this probe should be extended to:

1. **Protocol halt test**: send a malformed hcom message (missing required
   `--intent` on a broadcast request) through the future protocol
   validator; confirm it writes a `reason=validator_blocking_anomaly`
   record into the kill-switch halt store with `scope=task` (or `global`,
   per the finding's severity — see `map-validator-halt-state-spec.md`'s
   revised Blocking Storage section), and that `graph/runner.py` returns
   the kill-switch-blocked route for the affected task.
2. **Semantic halt test**: submit a deliberately defective output (e.g. a
   test that always passes trivially, disguised as real coverage) through
   the future Layer 1/Layer 2 cascade; confirm a halt row is written with
   `triggered_by=semantic_l1` or `semantic_l2` as appropriate.
3. **Clear-path test**: confirm the halt cannot self-clear — attempt to
   directly flip `status` to `CLEARED` in the DB without a Repair Record
   reference and confirm this is flagged as a violation the next time
   `SELF_REPAIR_SYSTEM.md`'s health-check report runs (a repair without a
   record is itself a `DRIFT`).
4. **False-positive path test**: adjudicate a halt as `false_positive` and
   confirm it clears without generating a Repair Record (per
   `map-validator-halt-state-spec.md`'s explicit rule that false positives
   are calibration data, not repairs).

## Why This Probe Is Split Into "Today" And "Future"

Per this task's own `map-validator-halt-state-spec.md`: the new validators
ship telemetry-only (non-blocking) until judge-accuracy data exists. A probe
claiming to demonstrate a full blocking halt for the semantic validator
before that data exists would be testing against a system that
deliberately isn't blocking yet — that would be a false "pass," not a real
one. This probe therefore documents what already halts (structural mirrors,
confirmed) and defines — but does not fake — the test for what will halt
once Waves 4's implementation lands.

## Related Files

- `MAP_System/artifacts/planning/map-validator-halt-state-spec.md` [[map-validator-halt-state-spec]]
- `MAP_System/artifacts/tests/map-613-simulation-testdrive-probes.md` [[map-613-simulation-testdrive-probes]]
- `MAP_System/scripts/validate_task_mirrors.py`
- `MAP_System/artifacts/reviews/task147-review-zera.md` [[task147-review-zera]]
