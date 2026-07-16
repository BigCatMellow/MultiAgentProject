# Work Packet: Real-Parameter Calibration + First Robustness Grading

Intended implementer: claude-lab-toku (source-mining auditor — context already loaded)
Dispatcher: claude-lab-mira (lead)
Status: awaiting task record (map_task.py create blocked by transient harness outage;
task ID will be assigned via --task-id auto and confirmed over hcom before you start)
Source: `artifacts/audits/source-mining-audit-2026-07-14.md` ranked item #1
(Gap-Register §3.1 — the 6.13 corpus's own top-ranked gap — plus Wave 2.5 grading)

## Goal

Replace "conditional" simulation-derived conclusions with measurements from the
real repo, and produce the first robustness grading report.

## Inputs (all exist)

- Measurement plan: `artifacts/audits/map-real-parameter-calibration.md`
- Grading method: `artifacts/audits/map-sensitivity-robustness-method.md`
- Data: `events/events.jsonl` (~1050 events), `map.db` task lifecycle
  (147+ tasks with claim/review/release timestamps), trace fields (TASK-170),
  `runtime/session_replay.sqlite` (queryable joined view)
- Semantic-validator false-positive question (Gap-Register §2a) folds in here

## Scope

1. Run every measurement in the calibration plan that current data supports
   (defect-vs-false-halt cost, misattribution rate, review-catch rate, latency
   per gate, operator-intervention frequency). Where data is insufficient,
   say so explicitly with what's missing — do NOT simulate substitutes.
2. Apply the robustness method to the standing 6.13-derived conclusions
   (eager-halt, validator split, routing) and label each
   robust/conditional/unsupported in a grading report.
3. Output: `artifacts/audits/map-real-parameter-calibration-results-2026-07-14.md`
   + `artifacts/audits/map-robustness-grading-2026-07-14.md`.

## Rules

- Read-only against all MAP state; your only writes are the two artifacts.
- Honest-negative results are wanted (TASK-174's "measurement inconclusive"
  section is the quality bar).
- Report to claude-lab-mira; independent review will follow normal gates.
