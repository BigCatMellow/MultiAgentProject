# MAP Runtime Migration Rollout Plan (TASK-148)

Owner: claude-lab-zera
Date: 2026-07-13
Input: `map-runtime-migration-inventory.md`, `map-613-master-implementation-plan.md`
Companion: `map-runtime-migration-smoke.md`

Purpose: order the MAP 6.13 implementation waves (TASK-147+) so each one
lands without repeating a repo-drift, two-copy, task-mirror, hcom-session, or
CommandCenterUI-desync incident. This is a sequencing and safety plan, not a
re-derivation of the waves themselves — see the master plan for scope.

## Guiding Rule

Every wave below follows the same shape: **freeze point → additive change →
validate → operator checkpoint → unfreeze**. No wave replaces or rewrites
existing rows/files in place; every new field is additive and nullable so
old data keeps validating.

## Order Of Operations

### Step 0 — Close the drift found during inventory (do first, blocks nothing else)

- Reconcile `map.db.agents` against `agents/status.json`: either (a) extend
  `scripts/reconcile_agents.py` to also read/write `map.db.agents`, or (b)
  add a small `register_agent()` helper in `db/claims.py` that both waves and
  new agent sessions call instead of ad hoc `INSERT`. Until this exists, any
  new agent session that tries to claim a task will hit the same FK failure
  this task hit.
- Freeze/lock point: none needed — additive only, no existing rows change.
- Rollback point: `DELETE FROM agents WHERE agent_id NOT IN (<status.json
  keys>)` is safe only for rows with no task history; do not delete rows with
  claims/heartbeats in `tasks.claimed_by` history.
- Validation command: `python3 MAP_System/scripts/reconcile_agents.py --hcom-json <(hcom list --json) --json`
  plus a manual diff of `map.db.agents` vs `status.json` keys.
- Do-not-proceed gate: do not start Wave 3 (cost governance, which needs a
  reliable per-agent identity to budget against) until this reconciliation
  exists.

### Step 1 — Wave 1 / 1.5 (single entry point, decomposer, subsystem API index, migration docs)

- Freeze point: none — these are new docs/scripts plus additive fields on
  `intake_request.py` output. No existing task/event schema changes yet.
- Validate: `scripts/validate_task_mirrors.py`, `scripts/validate_events.py`,
  `scripts/run_tests.sh`.
- Operator checkpoint: confirm the single-entry-point contract before any
  other wave starts assuming requests flow through it — Waves 4, 5, 8 all
  gate dispatch on this existing.
- Rollback point: revert the new doc/script files; no data migration to
  reverse.

### Step 2 — Wave 2 (trace schema, event append helper, real-parameter measurement)

- Freeze point: pause new hand-written `events.jsonl` appends for the
  duration of adding the new optional fields (`trace_id`, `parent_event_id`)
  to the schema and the append helper — otherwise agents write the old shape
  mid-migration and immediately generate new warnings.
- Additive change: add the new fields as optional in `validate_events.py`'s
  schema (mirroring how the existing warning-baseline mechanism already
  tolerates legacy lines); do not require them on historical lines.
- Validate: `scripts/validate_events.py --fail-on-new` must stay green
  against the existing 33-legacy-warning baseline; new lines missing the new
  optional fields should not raise new warnings until the fields become
  required in a later, explicit step.
- Operator checkpoint: review the real-parameter measurement report (Wave 2
  item 4) before Wave 6 (Library layer) or Wave 4 (eager-halt policy) treat
  any assumed number as validated.
- Rollback point: the append helper can be reverted independently of the
  schema fields; agents fall back to hand-written JSONL as before.

### Step 3 — Wave 3 (cost governance and kill switch)

- Depends on Step 0 (reliable agent identity) being done first.
- Freeze point: none for the additive event fields
  (`tokens_in`/`tokens_out`/`model_tier`/`estimated_cost`); freeze *dispatch*
  briefly only when first enabling budget enforcement (not just accounting)
  so no task is mid-claim when enforcement flips on.
- Operator checkpoint: the kill switch must default to "off"/no-op on first
  deploy and be exercised in a dry run before it can actually block dispatch
  — a first-day false-positive kill switch is worse than the incident it
  prevents.
- Do-not-proceed gate: do not enable the spend-rate circuit breaker in
  blocking mode until at least one full day of accounting-only data exists.

### Step 4 — Wave 4 (compliance verification and halt authority)

- Freeze point: before wiring halt state as a *blocking* dispatch gate,
  freeze new task claims briefly to confirm no task is left half-claimed
  under the old (non-halting) behavior.
- Do-not-proceed gate: per Gap-Register/simulation findings (Round R, files7)
  and the master plan's Wave 4, do not treat "more L1 deterministic rules"
  as a path to the ~1% false-positive target — that number depends on the
  L2 fuzzy judge, which is unmeasured. Do not flip halt to blocking-by-default
  until false-positive telemetry exists from an accounting-only period,
  mirroring Step 3's kill-switch caution.
- Rollback point: halt state should be a single flag/table row that can be
  force-cleared through the existing decision/authority path
  (`DECISION_AUTHORITY_SYSTEM.md`) without a code rollback.

### Step 5 — Wave 5 (gap scoring, emergence, local lanes) and Step 6 — Wave 6 (outcome feedback, Library layer)

- Freeze point: none — additive task metadata fields, gated by the
  promotion checks already in place (`scripts/promote_task.py`).
- Do-not-proceed gate (Library layer specifically): do not build any partial
  version. Round 3's simulation finding (summary-only is worse than no
  library) is a hard blocker on partial ship, not a preference — confirm
  compact summaries, wikilinks, and event-driven staleness invalidation all
  land in the same change before enabling the Library agent for any real
  document.
- Operator checkpoint: review the external-repo research pass (Repo-Review-List
  candidates: claude-bedrock, agentcairn, the hop-limit/budget-cap pattern,
  the WenyuChiou acceptance-gate comparison, codexia) before committing to a
  from-scratch Library implementation.

### Step 7 — Wave 7 (resilience controls: idempotency, dead-letter, circuit breaker, chaos tests, degradation policy)

- Freeze point: introduce idempotency keys additively (new optional column,
  ignored if absent) before any write path starts requiring them.
- Do-not-proceed gate: do not enable circuit breakers in blocking mode
  without first running the chaos-test suite (Wave 7 item 4) against a
  disposable copy of `map.db`, not the canonical one — this repo has a prior
  near-deletion incident on record; chaos/fault-injection testing must never
  target the canonical `map.db` or `events.jsonl` directly.
- Rollback point: dead-letter entries must be replayable back into `READY`
  status without hand-editing `task_graph.json`; build the replay path before
  relying on the dead-letter queue in production.

### Step 8 — Wave 8 (governance enforcement: pre-dispatch policy checker, destructive-action gates)

- Depends on Step 4 (halt authority) existing, since policy rejection uses
  the same blocking mechanism.
- Do-not-proceed gate: confirm `AGENT_PERMISSION_LEVELS.md`,
  `DESTRUCTIVE_ACTION_POLICY.md`, and `DECISION_CLASSES.md` are structured
  enough for the checker to parse reliably (inventory Section 10) before
  wiring it as a blocking gate — a policy checker that silently
  misinterprets prose is worse than no checker.

### Step 9 — Wave 9 (formal verification, failure-taxonomy coverage)

- No freeze needed — this wave produces specs/tests, not runtime schema
  changes. Can run in parallel with Steps 1-8 once Step 0-2 land, since it
  targets the allocator/lock/claim design that already exists.
- Include a sensitivity/robustness-grading pass (flagged by the simulation
  corroboration, not originally in the master plan) alongside the failure
  taxonomy matrix: grade which of the plan's load-bearing conclusions are
  structurally robust (safe to build on) vs. economically parameter-sensitive
  (recheck after Step 2's real-parameter measurement).

## CommandCenterUI Coordination

CommandCenterUI (`/home/home/Projects/CommandCenterUI`) is a separate
codebase and deploy lifecycle. Any wave whose output should be visible there
(Wave 1 single entry point, Wave 2 trace reconstruction, Wave 4 halt state,
the peripheral-review-flagged mission-control TUI concept) needs its own
follow-up task filed against that repo, coordinated the same way TASK-135
coordinated the ProjectUpdater integration — do not assume a MAP_System
change is visible in CommandCenterUI without a matching change there.

## Multi-Project (Pathwell) Checkpoint

Before Wave 3 (cost fields) or Wave 5 (task tiers) ship, the operator should
confirm whether budgets/tiers are global across all projects sharing this
repo (Pathwell included) or need a per-project dimension. Retrofitting a
project dimension onto live `tasks`/`events`/`agents` rows after those waves
ship is a second migration; deciding now avoids it.

## Operator Decision Points (summary)

1. Approve Step 0 agent-registration fix approach (extend
   `reconcile_agents.py` vs. new `register_agent()` helper).
2. Confirm budgets/tiers are global vs. per-project before Wave 3/5.
3. Confirm kill switch and halt authority both ship accounting-only before
   blocking mode (Steps 3-4).
4. Confirm CommandCenterUI follow-up tasks are filed separately, not folded
   into MAP_System task scope.
5. Confirm chaos tests (Wave 7) run only against disposable `map.db`/event-log
   copies, never canonical state.
