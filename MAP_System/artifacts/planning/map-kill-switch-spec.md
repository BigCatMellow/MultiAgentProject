# MAP Kill Switch Spec (TASK-151, Wave 3)

Status: draft-active
Owner: command-center
Built by: TASK-151

## Purpose

The kill switch is the emergency stop for runaway spend or unsafe autonomy.
It blocks dispatch through a small durable halt state that runner and agent
loops can read before claiming or launching new work. It is not a substitute
for task review, validation, or normal budget approval.

This is a design artifact only; TASK-151 does not create the halt store or
wire runner enforcement.

## Halt Storage

Recommended storage: a small JSON file or SQLite table with one active global
record. The implementation can choose the backend, but it must be durable,
human-inspectable, and validated.

Required fields:

| Field | Meaning |
|---|---|
| `halt_id` | Unique ID for this halt episode. |
| `state` | `clear`, `halt_paid_dispatch`, `halt_all_dispatch`, or `repair_only`. |
| `reason` | Short explanation, e.g. `spend_rate_breaker`, `operator_stop`, `validator_blocking_anomaly`. |
| `set_by` | Agent or command-center identity that set the halt. |
| `set_at` | UTC timestamp. |
| `scope` | `paid`, `project`, `task`, `agent`, or `global`. |
| `target` | Optional task/project/agent ID for scoped halts. |
| `clear_requires` | Required evidence before clearing. |
| `cleared_by` | Identity that cleared the halt, null while active. |
| `cleared_at` | UTC timestamp, null while active. |
| `clear_reason` | Evidence-backed reason for clearing. |
| `related_event_ids` | Events that caused or cleared the halt. |

## Who May Set Or Clear

| Action | Authority |
|---|---|
| Set `halt_paid_dispatch` for budget breach | Cost-governance implementation, core agent, or command-center. |
| Set `halt_all_dispatch` | command-center, or a blocking validator rule that has already been authorized for eager halt. |
| Set scoped task/agent halt | core agent or validator when evidence is specific and recorded. |
| Clear paid-dispatch halt | command-center, or core agent only when the halt policy explicitly allows clearing after objective evidence. |
| Clear global halt | command-center only. |
| Clear validator halt | authority named by the validator halt policy; normally requires repair/root-cause evidence. |

Core agents can recommend clearing a halt, but broad/global clears route
through the Decision / Authority System. Helpers and local models may never
clear halt state.

## Required Events

Every state transition must append an event with canonical fields plus trace
fields when available:

- `KILL_SWITCH_SET` or canonical equivalent if the event type registry has
  been extended;
- `KILL_SWITCH_CLEAR_REQUESTED`;
- `KILL_SWITCH_CLEARED`;
- `DISPATCH_BLOCKED_BY_KILL_SWITCH`;
- `DISPATCH_RESUMED_AFTER_KILL_SWITCH`.

Until event types are extended, use canonical `PROGRESS` or
`DECISION_RECORDED` events with explicit summaries and artifact paths. Do not
add non-canonical event types without updating `validate_events.py` and its
baseline behavior.

Event summaries must include:

- halt scope;
- reason;
- who set/cleared it;
- what dispatch lanes are still allowed;
- what evidence is required to clear it.

## Runner And Agent-Loop Response

Runner behavior:

1. Read halt state before recommending claims or helpers.
2. If `halt_paid_dispatch`, omit paid/core model dispatch from ready
   recommendations unless command-center approved a scoped override.
3. If `halt_all_dispatch`, route only to review, repair, operator decision,
   or read-only inspection tasks.
4. Include halt state in `next_route`, `recommended_action`, and mission
   control vitals.

Agent-loop behavior:

1. Check halt state before claiming a task.
2. If blocked, do not claim; append or surface a blocked-dispatch event.
3. If already working when a halt appears, finish only safe checkpointing:
   write handoff/state, stop paid calls, and request operator direction.
4. Do not clear the halt by editing files; call the sanctioned clear command.

Helper behavior:

- visible helpers may continue read-only review or inspection if the halt
  state permits it;
- local/no-cost helpers may continue only when the halt is cost-only and the
  task is explicitly safe;
- no helper may bypass a global halt.

## Relationship To Cost Governance

The cost spec owns budget counters and spend-rate breaker semantics. The kill
switch owns the durable halt flag that blocks dispatch. The normal flow is:

```text
cost telemetry -> spend-rate breaker -> halt state -> runner/agent-loop block
```

Failure and validator halts can also set halt state, but they are not cost
breakers. Keep the cause labels separate so mission control can distinguish
"too expensive" from "unsafe" from "corrupt state."

## Clear Conditions

Clearing a halt requires evidence:

| Halt reason | Clear evidence |
|---|---|
| `spend_rate_breaker` | current spend, revised limit or stopped paid work, operator approval if limit changes |
| `operator_stop` | explicit command-center clear |
| `validator_blocking_anomaly` | repair/root-cause record or adjudicated false positive |
| `stale_agent_reaper` | dead-letter/replay or reassignment record |
| `unknown_cost_paid_dispatch` | cost source fixed or paid dispatch disabled |

Clear commands must record who cleared the halt and why. A global clear
without evidence is a policy violation.

## First Implementation Constraints

- Start in accounting/dry-run mode.
- Do not block review, repair, or operator-decision paths unless the halt is
  global and explicit.
- Do not introduce a second task queue.
- Do not make the TUI the writer of halt state.
- Do not treat missing cost data as zero cost for paid lanes.
- Do not allow a local helper or spawned reviewer to clear a halt.

## Validation Path

Implementation tasks should add:

- schema validation for halt records;
- runner tests showing ready paid work is suppressed under halt;
- agent-loop tests showing claims are refused under halt;
- clear-command tests for authority and evidence requirements;
- event validation for every set/clear/block/resume transition.
