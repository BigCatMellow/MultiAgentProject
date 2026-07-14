<!-- hpom: file: ORCHESTRATION_ENTRYPOINT_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-13 -->
<!-- hpom: verified_against: TASK-147 -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Orchestration Entrypoint System

Status: draft-active
Owner: command-center
Built by: TASK-147

## What this is

This file defines the single intake surface for operator intent. It turns broad
human requests into protocol-shaped dispatch packets before agents treat them
as task authority.

## Core principle

```text
Operator intent enters once, is shaped once, and then fans out as explicit MAP
tasks or bounded agent requests.
```

## Entrypoint

The entrypoint is `scripts/intake_request.py`.

For every non-trivial operator request, intake should produce a dispatch packet
with:

- `request`
- `owner`
- `entrypoint`
- `classification`
- `decomposer_contract`
- `hcom_inform`

## Direct Message Policy

Direct operator-to-agent messages are allowed for attention and live control,
but broad work instructions must be converted into a dispatch packet before
agents use them as durable task authority.

Exceptions:

- emergency halt;
- approval/denial of an already-created gate;
- narrow status request;
- direct answer to a blocking question;
- trivial command that does not create durable work.

If a message asks more than one agent to do broad work, the first agent to start
must coordinate scope through hcom per `MAP_System/AGENTS.md`.

## Dispatch Packet

A valid dispatch packet names:

| Field | Purpose |
|---|---|
| `task_type` | planning, audit, implementation, research, review, maintenance |
| `risk_class` | PROCESS, KNOWLEDGE, SECURITY, DATA, AVAILABILITY |
| `gap_score` | low, medium, high |
| `task_tier` | shaping, local, core, helper, approval |
| `local_lane` | local support lane or `none` |
| `needs_approval` | whether dispatch requires command-center approval |
| `approval_reason` | why approval is required |
| `suggested_output_paths` | initial output path candidates |
| `acceptance_criteria_stub` | binary criteria to refine before claim |

## Relationship To Tasks

A dispatch packet is not a task by itself. It becomes one of:

- a `tasks/TASK-NNN.json` record;
- a bounded hcom request to a named agent;
- a helper note in `inbox/helpers/`;
- an operator question when scope or authority is unclear;
- a no-op when intake decides the request is informational only.

## Enforcement Goal

The target state is that agents can tell whether a work request is:

- already a MAP task;
- a dispatch packet ready to promote;
- a live operator decision;
- or unsupported chat context that must not become task authority yet.

## Related Files

- `scripts/intake_request.py`
- `artifacts/planning/map-decomposer-spec.md` [[map-decomposer-spec]]
- `shared/subsystem-apis.md` [[subsystem-apis]]
- `HUMAN_INTERFACE_SYSTEM.md` [[HUMAN_INTERFACE_SYSTEM]]
- `notes/communication-architecture.md` [[communication-architecture]]
- `MAP_System/AGENTS.md`
