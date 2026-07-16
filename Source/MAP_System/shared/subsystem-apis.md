<!-- hpom: file: shared/subsystem-apis.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-13 -->
<!-- hpom: verified_against: TASK-147 -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Subsystem APIs

Status: draft-active
Owner: command-center
Built by: TASK-147

## Purpose

This file names the service boundary each MAP subsystem exposes to working
agents. The goal is X-as-a-Service consumption: agents use platform functions
without rediscovering their internals.

## APIs

| Subsystem | Primary interface | Consumer responsibility |
|---|---|---|
| Intake | `scripts/intake_request.py` | Convert broad intent into dispatch packet before task authority |
| Allocator | `scripts/map_task.py create --task-id auto` | Reserve task IDs atomically through SQLite; do not hand-pick IDs without coordination |
| Task claims | `db/claims.py` | Claim, heartbeat, submit through SQLite; do not edit JSON to claim |
| Task graph | `workflow/task_graph.json`, `graph/runner.py` | Read route/queue state; update through supported task tools |
| Task mirrors | `migration/export_to_files.py`, `scripts/validate_task_mirrors.py` | Keep SQLite and file mirrors synchronized |
| Events | `events/events.jsonl`, `scripts/validate_events.py` | Append canonical event shape; preserve warning baseline |
| Validators | `scripts/validate_task_mirrors.py`, `scripts/validate_events.py`, `scripts/validate_task_graph.py`, `scripts/promote_task.py`, `scripts/release_task.py` | Run promotion, review, and release gates; treat validation failures as blockers until fixed or documented |
| Git operation lock | `scripts/git_operation_lock.py` | Use for repo-global operations |
| Emergence | `scripts/map_emergence.py`, `emergence/` | Capture real insights/ideas/experiments/synthesis; avoid ceremony |
| Local helpers | `scripts/local_runner.py`, `notes/local-model-helper-guide.md` | Use draft-only lanes; core agent remains accountable |
| Status | `agents/status.json`, `scripts/reconcile_agents.py`, `scripts/limit_watcher.py` | Keep agent availability and liveness synchronized before routing depends on status |
| Aider | `scripts/aider_wrapper.py` | Use only for narrow named-file edits after baseline checks |
| Decisions | `DECISION_AUTHORITY_SYSTEM.md`, `shared/decisions.md` | Record authority, class, owner, and supersession |
| Risk | `RISK_SYSTEM.md`, `shared/RISK_REGISTER.md` | Register open risks and acceptance path |
| Repair | `SELF_REPAIR_SYSTEM.md`, `repairs/` | Record drift/blocking/structural repairs |
| Research | `RESEARCH_SYSTEM.md`, `artifacts/research/` | Use for external, current, disputed, or sourced claims |
| Human interface | `HUMAN_INTERFACE_SYSTEM.md` | Surface decisions, risks, queues, agent state, and next actions |

## Rule

If an agent needs behavior not covered by an API here, it should add or update
the API as part of the task instead of relying on a private convention.
