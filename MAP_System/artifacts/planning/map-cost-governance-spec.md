# MAP Cost Governance Spec (TASK-151, Wave 3)

Status: draft-active
Owner: command-center
Built by: TASK-151

## Purpose

MAP needs cost visibility before broader autonomy. This spec defines the
event fields, budget counters, spend-rate breaker, override path, and
runaway-spend risk controls. It is design-only; no event schema or runner
enforcement changes are made by TASK-151.

## Cost Fields

Add these fields to future event records when cost data is available:

| Field | Type | Meaning |
|---|---|---|
| `tokens_in` | integer >= 0 | Input tokens consumed by the action. |
| `tokens_out` | integer >= 0 | Output tokens produced by the action. |
| `model_tier` | string | Cost lane such as `local`, `low`, `standard`, `premium`, `manual`, or `unknown`. |
| `estimated_cost` | number >= 0 | Estimated dollar cost for the action. Use `0` for local/no-cost work only when that is true. |
| `cost_source` | string | How the estimate was calculated: `provider_usage`, `static_rate`, `local_zero`, `manual_estimate`, or `unknown`. |
| `budget_scope` | string | `task`, `daily`, `project`, or `system`. |
| `budget_remaining` | number >= 0 | Remaining budget for the relevant scope after the event, when known. |

Compatibility rule: these fields start as recognized optional fields, not
required fields. Historical events and hand-written events must continue to
validate. Once an append helper reliably populates them, a later task can
move selected cost fields into warn-if-missing territory.

## Budget Scopes

| Scope | Counter key | Purpose |
|---|---|---|
| Per-task budget | `task_id` | Prevent one task or helper lane from consuming an unbounded budget. |
| Per-day budget | UTC date + project/system | Keep the whole MAP session under a daily operator budget. |
| Per-project budget | `project_id` | Future guard for Pathwell and other projects sharing MAP infrastructure. |
| Per-agent budget | `agent_id` + date | Detect one agent repeatedly choosing expensive paths. |

Initial enforcement order:

1. Accounting-only: record estimates and show warnings; never block.
2. Soft warning: add attention-queue items when 70% and 90% thresholds are
   crossed.
3. Approval gate: require operator approval before crossing 100% of a
   configured budget.
4. Spend-rate breaker: halt new paid dispatch when cost velocity is abnormal.

Budget values should live in a small config file or table owned by
command-center policy, not embedded in runner code. Defaults must be
conservative and easy to inspect.

## Spend-Rate Breaker

The cost circuit breaker watches cost velocity, not task failure.

Trigger candidates:

- estimated spend over a rolling one-hour window exceeds the configured
  hourly ceiling;
- per-day spend exceeds the daily ceiling;
- a single task consumes more than its per-task budget;
- cost events are missing or `cost_source=unknown` for paid model tiers;
- repeated budget override requests arrive within a short window.

Breaker states:

| State | Dispatch behavior |
|---|---|
| `accounting_only` | Record and report; do not block. |
| `warn` | Add attention item; dispatch continues. |
| `approval_required` | New paid work requires command-center approval. Local/no-cost and review work may continue if safe. |
| `halt_paid_dispatch` | Stop paid/core model dispatch; allow only operator, review, repair, and local inspection lanes. |
| `global_kill` | Defer to `map-kill-switch-spec.md`; all non-repair dispatch stops. |

The spend-rate breaker is distinct from the failure circuit breaker:

| Breaker | Watches | Primary risk | Default response |
|---|---|---|---|
| Cost breaker | token/cost velocity and budget exhaustion | runaway spend | pause paid dispatch or request approval |
| Failure breaker | stale agents, repeated validator failures, corruption, dead-letter volume | unsafe or broken execution | pause affected lane or task type |

They may both feed the same mission-control attention queue, but they must
have separate event types, thresholds, and clear paths.

## Operator Approval Path

Budget overrides are authority decisions, not routine task work.

Required request format:

```text
Issue: budget scope and current/forecast spend.
Options: stop, continue within local/no-cost lanes, approve one-time override, raise budget.
Recommendation: agent recommendation with cost/risk reason.
Needed: explicit command-center approval for the chosen override.
```

Override record fields:

- `approved_by`
- `approved_at`
- `budget_scope`
- `old_limit`
- `new_limit` or `one_time_extra`
- `expires_at`
- `reason`
- `related_task_id`
- `hcom_event_id`

Core agents may recommend overrides. Only command-center can approve
AUTHORITY/POLICY-level budget increases or clear a spend-rate breaker.

## Required Events

Future implementation should emit canonical events for:

- budget accounting updates that cross warning thresholds;
- budget override requested;
- budget override approved/denied;
- spend-rate breaker entered;
- spend-rate breaker cleared;
- paid dispatch blocked due to budget;
- paid dispatch resumed.

Events should include TASK-149 trace fields when available and cost fields
when known. Event validation must preserve legacy compatibility.

## Risk Note: Runaway Spend

Risk: once MAP can decompose, dispatch helpers, and continue across multiple
agents, a bad loop can convert a small operator request into repeated paid
model calls before the operator notices.

Impact: direct monetary loss, operator trust loss, and hidden opportunity cost
from agents spending time on low-value loops.

Mitigations:

- accounting-only telemetry before blocking enforcement;
- visible per-task and per-day budget counters;
- spend-rate breaker separate from failure breaker;
- command-center approval for budget overrides;
- local/no-cost lane fallback when paid dispatch halts;
- canonical events for every override and breaker transition;
- mission-control attention item for budget breach or unknown paid cost;
- kill switch for global stop if spend is no longer bounded.

Residual risk: cost estimates may be delayed or unavailable from provider
usage APIs. When model tier is paid and cost is unknown, the system should
treat the event as higher risk, not as zero cost.

## Validation Path

Implementation tasks should add:

- event validator recognition for cost fields;
- tests for malformed negative/non-numeric cost fields;
- runner/agent-loop checks that consult budget state before paid dispatch;
- fixtures proving local/no-cost lanes continue when only paid dispatch is
  halted;
- operator override records that can be audited from events and decisions.
