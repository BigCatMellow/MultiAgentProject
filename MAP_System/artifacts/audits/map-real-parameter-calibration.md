# MAP Real-Parameter Calibration Plan (TASK-149, Wave 2)

Status: draft-active
Owner: command-center
Built by: TASK-149

## Purpose

The 6.13 Gap Register's #1-ranked, highest-value open item: every simulation
conclusion (Rounds 1-6) was validated against *assumed* parameters, never the
real repository. This is the measurement plan, not the measurement itself —
running it is follow-on work once the trace/event infrastructure (this task)
and enough real task history exist to measure against.

## The Four (Now Seven) Parameters To Measure

Per the master plan and Gap-Register/Round-6, in priority order (highest
leverage first — the two flagged by Round 6 as flipping conditional
conclusions get measured first):

### 1. Compression ratio (decides C2 — Library layer payoff)

- What: for a sample of MAP shared docs (`shared/`, `notes/`, systems docs
  like `RESEARCH_SYSTEM.md`), the ratio of a hand-written compact summary's
  length to the full document's length.
- How: pick 10-15 representative docs across sizes; write or generate a
  summary; measure token/character ratio.
- Threshold from Round 6: Library layer pays off only when compression is
  meaningfully above ~2x AND churn is not low. Below that, skip Wave 6's
  Library layer for this corpus.

### 2. File churn rate (decides C2 alongside compression)

- What: how often shared/systems docs actually change per week/month.
- How: `git log --follow --format=%ad -- <path>` per doc, or a repo-wide
  `git log --since=... --name-only` scan bucketed by directory
  (`shared/`, root `*_SYSTEM.md`, `notes/`).
- Low churn + low compression = do not build the Library layer yet.

### 3. Emergence misattribution rate (decides C4 — pruning guard necessity)

- What: of Emergence's captured insights/ideas that were later promoted and
  then reworked or rejected, how many were attributed to the wrong root
  cause.
- How: sample `emergence/ideas/`, `emergence/insights/`, cross-reference
  against later task rework/rejection events once the trace schema (this
  task's other output) lets that cross-reference happen automatically.
- Round 6 threshold: above ~20% misattribution, keep/build the pruning
  guard; below, it is close to neutral and optional.

### 4. Shipped-defect vs. false-halt cost ratio

- What: relative cost (in rework time/tokens) of a real defect reaching
  release vs. a validator false-halt blocking good work.
- How: once Wave 4's compliance/halt validator exists and produces
  telemetry (`true_positive`/`false_positive`/`waived` adjudication per the
  master plan), tally real incidents on both sides over a measurement
  window.
- This one cannot be measured yet — it depends on Wave 4 shipping first.
  Record as blocked-on-Wave-4 rather than skipped.

### 5. Local-vs-cloud defect rate

- What: for tasks or subtasks routed to local/Ollama helpers vs. core
  agents, the rate of defects found post-hoc.
- How: once task-tier metadata (Wave 5) exists, compare outcome-feedback
  events (Wave 6) grouped by `task_tier`/`local_lane`.
- Blocked on Wave 5/6 shipping.

### 6. Wall-clock latency (Gap-Register Bucket 3.3, "never touched")

- What: real end-to-end task duration, not token/work-unit cost — the
  single-entry-point orchestrator's main risk (a throughput bottleneck) was
  never measured in any simulation round.
- How: `created_at` timestamps already exist per event; once `trace_id`
  groups a task's full event chain (this task's schema), duration is
  `max(created_at) - min(created_at)` per trace. Can be approximated today
  by `task_id` grouping even before trace adoption is complete.

### 7. Operator approval load (Gap-Register Bucket 3.5)

- What: total real attention load across emergence suggestions + governance
  approvals + validator escalations, and how often the operator is simply
  absent when a gate is waiting.
- How: count `needs_approval`/approval-gate events per day/week once Wave 3
  (cost governance) and Wave 8 (governance enforcement) emit them
  consistently; cross-reference against `agents/status.json` operator
  availability windows.

## hcom Volume (mentioned in acceptance criteria, separate from the 7 above)

- What: ratio of point-to-point hcom messages to shared-state
  reads/writes — the direct test of Principle 1 ("coordinate through
  directly-readable shared state, not relayed messages").
- How: `hcom events --last N` or the event log's `sender`/`type` distribution
  vs. count of task/file mirror updates in the same window. This is
  measurable today with no further infrastructure — recommend running it
  first as a quick real-data check on Principle 1 adherence.

## What This Task Delivers vs. What It Doesn't

This document is the plan and method. It does NOT contain a completed
measurement, because:

- Parameters 4 and 5 are blocked on Wave 4/5/6 shipping first (measuring
  them before those exist would just re-assume the numbers).
- Parameters 1, 2, 3, 6, and hcom volume can be measured now, but doing so
  rigorously (representative sampling, not cherry-picking) is a bounded
  follow-on task, not a side effect of writing this plan.

## Recommended Follow-On Task

File a task (Wave 2 item 4 candidate) titled "Measure MAP real-repo
parameters (batch 1: compression, churn, hcom volume, latency)" scoped to
the 4 parameters measurable today, with this document as its method
reference. Do not fold parameters 4-5 into that task; they wait for Wave
4-6.

## Related Files

- `Guidelines/6.13/files8/MAP-Simulation-Results-Round6.md`
- `Guidelines/6.13/MAP-Gap-Register.md`
- `MAP_System/artifacts/planning/map-613-master-implementation-plan.md` [[map-613-master-implementation-plan]] (Wave 2)
- `MAP_System/artifacts/audits/map-sensitivity-robustness-method.md` [[map-sensitivity-robustness-method]]
