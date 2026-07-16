# MAP Resilience Controls Spec (TASK-155, Wave 7)

Status: draft-active
Owner: command-center
Built by: TASK-155

## Purpose

MAP needs failure handling that preserves canonical state when agents crash,
helpers fail, validators disagree, or shared files drift from SQLite. This
spec defines the runtime controls: idempotency registry, dead-letter queue,
failure circuit breakers, and blast-radius containment.

This is a design artifact only. TASK-155 does not create new tables or change
dispatch behavior.

## Control Surfaces

| Control | Owns | Primary risk |
|---|---|---|
| Idempotency registry | duplicate write suppression and replay safety | silent double-applied task/event/mirror writes |
| Dead-letter queue | recoverable failed work records | crashed or timed-out work disappearing |
| Failure circuit breaker | temporary pause of broken agents/subsystems | repeated bad dispatch into known failure |
| Blast-radius containment | quarantine and scoped halt rules | one corrupt write poisoning downstream work |

Round 4 chaos results validated all four controls under heavy fault load.
Blast-radius containment carried the largest cascade risk, dead-lettering
prevented lost work, idempotency prevented invisible double-applies, and the
circuit breaker mattered when one agent or subsystem was persistently sick.

## Idempotency Registry

Every sanctioned write helper that can be retried should accept an
`idempotency_key`. The key identifies intent, not process attempt.

Recommended key shape:

```text
<task_id>:<writer_id>:<operation>:<stable_target>:<content_hash_or_step_id>
```

Examples:

- `TASK-155:codex-lab-mozu:event:SUBMISSION:artifact-hash`
- `TASK-155:agent_loop:submit_task:TASK-155:step-submit`
- `TASK-155:exporter:export_to_files:task-mirror:db-revision`

Registry record fields:

| Field | Meaning |
|---|---|
| `idempotency_key` | Unique stable key for one logical write. |
| `operation` | Helper operation such as `append_event`, `submit_task`, `export_to_files`, or `dead_letter`. |
| `target` | Task ID, path, DB row, or queue record affected. |
| `writer_id` | Agent or service identity requesting the write. |
| `request_hash` | Hash of semantic request payload. |
| `result_hash` | Hash of applied result, if successful. |
| `status` | `started`, `applied`, `duplicate_ignored`, `conflict`, or `failed`. |
| `created_at` | UTC timestamp for the first attempt. |
| `last_seen_at` | UTC timestamp for the most recent retry. |
| `related_event_ids` | Events that describe the operation. |

Retry rules:

- If the same key and same request hash already has `applied`, return the
  prior result and do not write again.
- If the same key has a different request hash, stop with `conflict`; do not
  guess which intent is correct.
- If the prior status is `started` but stale, require a checkpoint check
  before replaying.
- Idempotency must wrap both SQLite writes and file mirror/export writes.

## Dead-Letter Queue

Dead-lettering captures recoverable work that cannot safely be returned to
normal dispatch. It is not a trash folder; every record needs replay or
closure instructions.

Initial storage may be either a SQLite table or append-only files under
`MAP_System/dead_letters/`. The store must be durable, inspectable, and
validated before enforcement depends on it.

Record fields:

| Field | Meaning |
|---|---|
| `dead_letter_id` | Unique queue ID. |
| `task_id` | Affected task. |
| `agent_id` | Last known owner or subsystem. |
| `detected_at` | UTC timestamp. |
| `reason` | `handler_crash`, `lease_reclaimed`, `repeated_failure`, `poisoned_state`, `validator_halt`, or `manual_quarantine`. |
| `attempt_count` | Attempts known before dead-lettering. |
| `last_checkpoint_id` | Last durable completed step, if any. |
| `artifact_paths` | Relevant output, handoff, transcript, or repair paths. |
| `idempotency_keys` | Keys that must be checked before replay. |
| `replay_policy` | `return_ready`, `resume_from_checkpoint`, `create_repair_task`, `operator_decision`, or `close_unreplayable`. |
| `replay_status` | `queued`, `replayed`, `closed`, or `blocked`. |

Dead-letter triggers:

- agent-loop handler exits nonzero repeatedly past retry policy;
- liveness reaper reclaims the same task or agent repeatedly;
- a validator detects malformed protocol output or mirror drift that cannot
  be mechanically repaired;
- an idempotency conflict appears;
- a committed output is quarantined as poisoned state.

Replay must happen through sanctioned task transitions and write helpers. It
must never require manual JSON edits to task mirrors.

## Failure Circuit Breakers

Circuit breakers are scoped pauses, not global panic by default. They consume
structured signals from liveness, validators, dead letters, cost governance,
and local helper health.

Inputs:

| Input | Source | Example trigger |
|---|---|---|
| `agent_repeated_stale` | liveness reaper | same agent reclaimed twice in a rolling window |
| `agent_handler_failure_rate` | agent loop | N handler failures for same agent/task lane |
| `subsystem_validator_failures` | validators | repeated task mirror or event validation failure |
| `dead_letter_volume` | dead-letter queue | queue grows past threshold or same reason repeats |
| `poisoned_state_detected` | self-repair / validators | committed output causes downstream validation failure |
| `local_model_unhealthy` | local assistant health | repeated local helper timeout or malformed output |

States:

| State | Dispatch behavior |
|---|---|
| `accounting_only` | Record breaker inputs; do not block. |
| `warn` | Add attention item; dispatch continues. |
| `scoped_pause` | Stop dispatch only to the affected agent, helper lane, task type, or subsystem. |
| `repair_only` | Allow read-only review and repair tasks for the affected scope. |
| `global_halt` | Delegate to `map-kill-switch-spec.md`; only command-center or approved validator policy can set this. |

Actions:

- mark an agent or subsystem unavailable in runner-visible state;
- suppress affected tasks from `ready_tasks` and surface them as waiting;
- create or update a dead-letter record for failed work;
- request operator action only when the pause is structural, global, or lacks
  an approved clear condition;
- require objective clear evidence before returning to normal dispatch.

Clear evidence can include successful validator reruns, replay closure,
healthy liveness window, repaired state record, or command-center approval.

## Blast-Radius Containment

Containment prevents one bad write from becoming project truth for every
downstream agent.

Expectations:

- Canonical writes go through helpers that validate inputs and emit events.
- File mirrors are derived from SQLite and reconciled after task transitions.
- A validator failure on canonical state fails closed for new writes until
  repaired or explicitly scoped.
- Suspect artifacts are quarantined by path or task ID before downstream
  tasks consume them.
- Repair records distinguish mechanical drift from structural corrections.
- Runner should prefer `repair_only` or `wait_or_reconcile` over dispatching
  work whose dependencies read quarantined outputs.

Containment levels:

| Level | Use when | Allowed work |
|---|---|---|
| `artifact_quarantine` | one output path is suspect | unrelated tasks; repair/review of suspect path |
| `task_quarantine` | one task's outputs or transition are suspect | unrelated tasks; task repair/replay |
| `lane_pause` | one agent/helper/subsystem is bad | other lanes; scoped repair |
| `canonical_store_halt` | SQLite/events/mirrors cannot be trusted | read-only inspection from snapshots; no writes |

The default is the smallest scope that prevents cascade. Broad halts require
clear evidence because they can block unrelated work.

## Event And Validation Expectations

Implementation tasks should add validation for:

- idempotency record schema and duplicate/conflict behavior;
- dead-letter record schema and replay status vocabulary;
- breaker state records and clear evidence;
- quarantine records with explicit scope and affected paths;
- task graph response when quarantined dependencies exist.

Until event types are extended, use canonical event types with explicit
summaries and artifact paths. Do not add new event types without updating
`validate_events.py` and its baseline.
