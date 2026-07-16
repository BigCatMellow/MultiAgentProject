# MAP Validator Halt-State Spec (TASK-152, Wave 4)

Status: draft-active
Owner: command-center
Built by: TASK-152
Companion: `map-protocol-validator-spec.md`, `map-semantic-validator-spec.md`

## Purpose

Defines blocking storage, runner/agent-loop response, root-cause/repair
requirement, and clear authority for validator-triggered halts — the
mechanical answer to "can the validator actually halt, or only log?"
(Simulation-TestDrive's Probe 2, `map-613-simulation-testdrive-probes.md`).

## Blocking Storage — Reuses The Kill-Switch Halt Store (TASK-151), Does Not Fork It

**Revision note (found during this task's own validation pass):** TASK-151's
already-approved `map-kill-switch-spec.md` defines a general durable halt
store with `scope` (`paid`/`project`/`task`/`agent`/`global`) and a `reason`
field whose worked example table already lists
`validator_blocking_anomaly` as a clear-condition case. An earlier draft of
this spec independently invented a second table, `validator_halts`, before
that cross-check was done. Two parallel halt stores would mean the runner
and agent-loop each need to check two places before dispatch, and mission
control would need to reconcile which one is authoritative — exactly the
single-source-of-truth violation Principle 1 warns against. This is
corrected here: **validator halts are one more producer into the kill
switch's existing halt store, not a separate table.**

- Location: the halt store defined by `map-kill-switch-spec.md` (JSON file
  or SQLite table with one active global record per scope, per that spec).
  No new top-level halt table is added by this task.
- When a protocol or semantic validator finding warrants a halt, it writes
  a record into that store with:
  - `scope`: `task` (task-scoped) or `global` (repo-wide, e.g. a
    STRUCTURAL finding disputing already-released work);
  - `reason`: `validator_blocking_anomaly` (reusing the kill-switch spec's
    existing reason vocabulary, not inventing a new one);
  - `set_by`: the validator/agent identity that detected the anomaly.
- Validator-specific detail that the kill-switch's generic fields don't
  carry — `triggered_by` (`protocol` | `semantic_l1` | `semantic_l2`) and
  `severity` (reusing `SELF_REPAIR_SYSTEM.md`'s `DRIFT`/`BLOCKING`/
  `STRUCTURAL` vocabulary) — is carried in the kill-switch record's
  `related_event_ids` (pointing to a canonical event that has these fields
  in its summary/artifact_paths) rather than as new halt-store columns.
  This keeps the halt store's schema owned by one task (TASK-151) while
  still letting a validator halt be fully diagnosable.
- `clear_requires` (already a field in the kill-switch spec) is set to the
  Root-Cause/Repair Requirement below when a validator sets the halt.

## Runner / Agent-Loop Response

This reuses `map-kill-switch-spec.md`'s existing runner/agent-loop response
design (Runner behavior items 1-4, Agent-loop behavior items 1-4) — a
validator halt is just one more `reason` value the runner already has to
check for. No second check is added to `graph/runner.py` or
`scripts/agent_loop.py`; a validator halt with `scope=global` behaves like
`halt_all_dispatch`/`halt_paid_dispatch` there, and `scope=task` behaves
like the kill-switch spec's "scoped task/agent halt."

Mapping this task's severity vocabulary onto that shared behavior:

- A `DRIFT`-severity finding does NOT set a halt at all (mirrors
  Self-Repair's rule that `DRIFT` is auto-repairable without escalation) —
  it is telemetry only, surfaced in mission control, no kill-switch record
  written.
- A `BLOCKING`-severity finding sets a `scope=task` halt via the kill-switch
  store — blocks that task's claim/heartbeat/submit path only (reuse
  `claim_block_reason()`'s existing pattern in `db/claims.py`, adding
  "task has an open kill-switch halt record" as one more check, the same
  integration point the kill-switch spec already calls for).
- A `STRUCTURAL`-severity finding sets a `scope=global` halt — the runner's
  existing kill-switch handling already routes this to
  review/repair/operator-decision-only, matching how a `STRUCTURAL`
  Self-Repair finding already requires stopping and escalating.

## Root-Cause / Repair Requirement

A halt cannot clear itself. Per `SELF_REPAIR_SYSTEM.md`'s existing
authority tiers, applied here:

- `DRIFT`-severity halt: any core agent may clear after a mechanical fix,
  logging a Repair Record (existing convention, reused as-is).
- `BLOCKING`-severity halt: requires either a mechanical fix + Repair
  Record (Tier 1 core agent, same as Self-Repair's existing `BLOCKING` rule)
  or, if the fix requires judgment, a proposed fix posted via hcom
  `--intent request` before acting.
- `STRUCTURAL`-severity halt (e.g. a semantic L2 finding disputes something
  already approved/released): escalates to command-center per
  `DECISION_AUTHORITY_SYSTEM.md`, same as any other `STRUCTURAL` Self-Repair
  item. No core agent clears this unilaterally.
- Every clear references: what was found, which validator surfaced it,
  what was changed, what was verified after (reusing the existing Repair
  Record template's four required fields — no new template needed).

## Clear Authority

| Severity | Who may clear | Record required |
|---|---|---|
| `DRIFT` | Any core agent | Repair Record |
| `BLOCKING` (mechanical fix) | Any core agent | Repair Record |
| `BLOCKING` (judgment fix) | Core agent, after hcom `--intent request` proposal | Repair Record + hcom thread reference |
| `STRUCTURAL` | Command-center only | Repair Record + decision entry in `shared/decisions.md` |

This table is directly `SELF_REPAIR_SYSTEM.md`'s existing authority ladder
applied to validator halts specifically — no new authority model invented,
per that system's own principle: "MAP cannot silently rewrite its own
authority."

## False-Positive Path (does not create a halt)

If a triggered halt is adjudicated `false_positive` (see
`map-protocol-validator-spec.md`'s and `map-semantic-validator-spec.md`'s
adjudication fields), it clears immediately with `cleared_by` = the
adjudicating agent and no Repair Record — a false positive is calibration
data for judge accuracy, not a repair. This distinction matters: conflating
false-positive clears with real repairs would corrupt the repair-recurrence
tracking `SELF_REPAIR_SYSTEM.md` already relies on ("Follow-up prevention").

## Why This Doesn't Ship As Blocking-By-Default On Day One

Per `map-runtime-migration-plan.md`'s Step 4 (this task's own migration
rollout plan, written under TASK-148): do not flip halt to blocking-by-
default until false-positive telemetry exists from an accounting-only
period. The table/schema above should ship with `severity` capped at
`DRIFT` (non-blocking, telemetry-only) until the semantic validator's L2
judge accuracy is measured — otherwise the very first false positive from
an unmeasured judge halts real dispatch.

## Related Files

- `MAP_System/artifacts/planning/map-kill-switch-spec.md` [[map-kill-switch-spec]] (TASK-151 — owns
  the actual halt store this spec writes into)
- `MAP_System/SELF_REPAIR_SYSTEM.md` [[SELF_REPAIR_SYSTEM]]
- `MAP_System/DECISION_AUTHORITY_SYSTEM.md` [[DECISION_AUTHORITY_SYSTEM]]
- `MAP_System/db/claims.py` (`claim_block_reason`)
- `MAP_System/graph/runner.py`
- `MAP_System/artifacts/planning/map-runtime-migration-plan.md` [[map-runtime-migration-plan]] (Step 4)
- `MAP_System/artifacts/tests/map-validator-halt-probe.md` [[map-validator-halt-probe]]
