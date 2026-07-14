# MAP Liveness Reaper Spec (TASK-150, Wave 2.5)

Status: draft-active
Owner: command-center
Built by: TASK-150

## Purpose

MAP already has partial liveness machinery in `scripts/limit_watcher.py`:
it reads hcom session status, detects some silent stops, nudges stalled
agents, and writes events. TASK-150 defines the next runtime contract: a
durable liveness surface that mission-control can read and a reaper policy
that can recover or dead-letter stale work without relying on chat memory.

This is a specification only. It does not change the current watcher or task
claim behavior.

## Liveness State

Each live core agent should have one durable status record, derived from
`agents/status.json`, hcom status, and task claim state. The mission-control
view reads this surface; it does not become the owner of it.

Required fields:

| Field | Meaning | Source |
|---|---|---|
| `agent_id` | Canonical hcom/MAP agent name, e.g. `codex-lab-mozu`. | `agents/status.json`, hcom |
| `last_seen` | Last observed activity or heartbeat timestamp in UTC. | hcom status/event stream, future heartbeat helper |
| `active_task` | Current claimed task ID, or null. | `map.db.tasks.claimed_by` |
| `lane` | Routing lane: `core`, `helper`, `local`, `review`, `operator`, or `service`. | task role, helper notes, `agents/README.md` identity kind |
| `state` | State vocabulary below. | derived |
| `state_since` | First timestamp this state was observed. | liveness helper |
| `stale_after` | Timestamp when the current heartbeat becomes stale. | derived from timeout policy |
| `evidence` | Short source note, e.g. `hcom:listening`, `task:IN_PROGRESS`, `status:awaiting_work`. | derived |

State vocabulary:

| State | Definition | Operator meaning |
|---|---|---|
| `alive` | hcom process is live and recent, with no active claimed task. | Available/idle. |
| `working` | agent owns an `IN_PROGRESS` task and heartbeat is fresh. | Normal. |
| `blocked` | agent is live but waiting on a request, approval, prompt, or declared blocker. | Needs triage only if the blocker requires operator action. |
| `idle` | agent is live/listening, no active task, no declared standby reason, beyond the check-in threshold. | Candidate for work dispatch or standby declaration. |
| `suspect` | heartbeat or hcom status is stale but the reaper has not acted yet. | Watch closely; attention queue item. |
| `broken` | repeated stale/silent behavior, failed resume probes, or dead-lettered task ownership. | Circuit-breaker input; human-visible. |
| `standby` | agent deliberately declared unavailable or awaiting work. | Do not nudge unless matching a scheduled resume policy. |

## Timeout Policy

Initial defaults should mirror existing `limit_watcher.py` behavior:

- Fresh hcom status: live if hcom reports `active`, `listening`, `waiting`,
  or `blocked` and the process is bound.
- Stale hcom fallback: if hcom lacks process-bound data, `status_age_seconds`
  greater than 1800 seconds is `suspect`.
- Idle check-in: a live/listening agent with no claim and no standby reason
  for 7200 seconds becomes `idle`.
- Work nudge throttle: while actionable work exists, nudge an idle agent at
  most once every 1800 seconds and never before it has been idle for at least
  120 seconds.

These values are defaults, not policy constants. Mission-control must display
the effective timeout alongside the state so an operator can tell whether a
red status is seconds old or hours old.

## Reaper Action

The reaper is a gated policy, not a free-form cleanup script. It must write a
canonical event for every action and keep task mirrors valid after acting.

Recommended action ladder:

1. `suspect`: mark the agent suspect and surface an attention item. Do not
   mutate task ownership on the first stale heartbeat.
2. `nudge`: send a visible hcom resume/check-in through the existing RnS
   mechanism. Resume commands must use visible terminals, never headless.
3. `reclaim`: if the agent owns an `IN_PROGRESS` task and remains stale after
   the reclaim timeout, clear the claim only through a sanctioned DB helper,
   return the task to `READY`, and append a `PROGRESS` or future
   `DEAD_LETTER` event explaining the evidence.
4. `dead-letter`: if reclaiming would lose context, move the task into a
   dead-letter queue with the last known owner, lease, task, output paths,
   and transcript/handoff pointers. A replay path must exist before blocking
   production behavior depends on this queue.
5. `broken`: after repeated stale/reclaim cycles, mark the agent broken and
   emit a circuit-breaker signal.

Manual JSON edits to `tasks/TASK-*.json` or `workflow/task_graph.json` are
not reaper actions. Reaper writes must go through SQLite helpers and then
`migration/export_to_files.py`, followed by `validate_task_mirrors.py`.

## Dead-Letter Record

Dead-letter records should be append-only files or DB rows with:

- `dead_letter_id`
- `task_id`
- `agent_id`
- `detected_at`
- `last_seen`
- `last_heartbeat_at`
- `lease_expires_at`
- `reason`
- `replay_status`
- `artifact_paths`
- `handoff_paths`
- `hcom_event_ids`
- `replay_command`

Replay must restore the task through a supported transition, normally back to
`READY` or into a bounded repair task. It must not require hand-editing the
task graph.

## Circuit-Breaker Signal

The reaper feeds Wave 7 resilience and Wave 3 cost governance with structured
signals:

| Signal | Meaning |
|---|---|
| `agent_stale_once` | One stale incident, recovered by nudge or timeout. |
| `agent_reclaimed_task` | Reaper had to return or dead-letter claimed work. |
| `agent_repeated_stale` | Multiple stale incidents within a rolling window. |
| `agent_broken` | Agent should stop receiving new work until reviewed. |
| `system_liveness_degraded` | More than one core lane stale or broken at once. |

Circuit breakers should start accounting-only. Blocking dispatch based on
these signals waits for the Wave 7 resilience task and a dry run against
non-canonical data.

## Mission-Control Consumption

Mission-control reads this liveness state to render:

- green/fresh heartbeat for `alive` and `working`;
- yellow for `idle`, `blocked`, and `suspect`;
- red for `broken` or dead-lettered work;
- grey for deliberate `standby`.

The TUI may initiate future interventions only by calling the same sanctioned
commands the CLI uses. Until the read-only view is accurate, all intervention
keys remain disabled or dry-run only.
