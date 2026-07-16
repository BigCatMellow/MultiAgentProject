# MAP Durable Execution Spec (TASK-155, Wave 7)

Status: draft-active
Owner: command-center
Built by: TASK-155

## Purpose

`scripts/agent_loop.py` already has a LangGraph checkpointer, task leases,
heartbeats, retry cooldowns, and export-after-submit behavior. Durable
execution extends that shape so long-running work can resume after a process
restart without double-applying partial writes.

This is a design artifact only. TASK-155 does not change the agent loop.

## Scope

Durable execution applies first to MAP runtime tasks that mutate canonical
state:

- task claim, release, submit, approve, and export;
- event append;
- dead-letter and replay transitions;
- repair records that mutate task or mirror state;
- future decomposer/intake task creation.

General editing work can remain human/agent-driven until task duration and
failure rates justify broader checkpointing.

## Checkpoint Model

Each durable operation is a sequence of named steps. A step is complete only
after its canonical write and validation evidence are durable.

Step record fields:

| Field | Meaning |
|---|---|
| `execution_id` | Stable ID for one task attempt or replay. |
| `task_id` | Task being worked. |
| `agent_id` | Agent or service performing the step. |
| `step_id` | Stable name such as `claim`, `write-artifacts`, `append-submission-event`, `export-mirrors`. |
| `idempotency_key` | Key guarding the step's write. |
| `status` | `pending`, `started`, `completed`, `failed`, or `skipped_duplicate`. |
| `started_at` | UTC timestamp. |
| `completed_at` | UTC timestamp, if completed. |
| `inputs_hash` | Hash of semantic step inputs. |
| `outputs_hash` | Hash of applied outputs, if any. |
| `evidence_paths` | Files, event IDs, or validation logs proving completion. |

For an agent-loop submission, the minimum durable step chain is:

1. `claim`: task claim and lease established.
2. `handler-start`: handler command and execution ID recorded.
3. `checkpoint-work`: optional handoff/artifact checkpoint emitted by the
   handler for long tasks.
4. `submit-task`: `submit_task` succeeds using an idempotency key.
5. `append-submission-event`: event is recorded once.
6. `export-mirrors`: `migration/export_to_files.py` completes.
7. `validate-mirrors`: task mirror validator passes or failure is dead-lettered.

## Event Replay Resume

Resume is evidence-driven, not memory-driven. On restart, the runner or agent
loop should read:

- latest checkpoint records for `execution_id` or `task_id`;
- canonical task row from SQLite;
- event log entries for claim/progress/submission/review/repair;
- dead-letter records for the task or agent;
- file mirror validation status.

Resume algorithm:

1. Load the task row and latest execution record.
2. If the task is terminal, return terminal state and do not replay writes.
3. If a completed step has a matching idempotency key and result hash, skip it.
4. If a started step has no completion and the lease is fresh, do not steal it.
5. If a started step is stale, compare canonical state and event log evidence.
6. Resume at the first incomplete step whose preconditions still match.
7. If evidence conflicts, stop and create a dead-letter or repair record.

Event replay should reconstruct decisions, not re-run arbitrary shell
commands. Handler commands may be rerun only when the task declares the step
idempotent or the operator/core agent supplies a replay policy.

## Idempotency Safety For Partial Retries

Partial retries must be safe at every write boundary.

Rules:

- Generate an idempotency key before a write starts and record it in the
  checkpoint.
- Use one key per logical write, not one key for an entire multi-step task.
- Never reuse a key for different semantic content.
- Treat same key plus different request hash as a conflict and halt the replay.
- Treat same key plus same request hash as a duplicate and return the prior
  result.
- Export/reconciliation steps use keys tied to the DB revision or source
  state hash so stale exports do not overwrite newer state.

Example:

```text
TASK-155:codex-lab-mozu:submit_task:TASK-155:step-submit
TASK-155:codex-lab-mozu:append_event:SUBMISSION:artifact-set-hash
TASK-155:exporter:export_to_files:map.db-revision-<rev>
```

## Handler Checkpoints

A long-running handler should checkpoint only stable facts:

- claimed task ID and owner;
- completed substeps;
- artifact paths written;
- tests or validators already run;
- hcom event IDs for coordination;
- outstanding blockers or approvals.

Checkpoint files should live under a future `MAP_System/checkpoints/` or a
SQLite table, not in chat-only context. A checkpoint is not task completion;
it is resume evidence.

## Dead-Letter On Ambiguous Resume

Resume must fail closed when it cannot prove the next safe step.

Dead-letter instead of replay when:

- task row and event log disagree about terminal state;
- idempotency registry has a conflict;
- a stale export may overwrite newer DB state;
- a handler wrote artifacts but did not record enough evidence to know whether
  they are final;
- validation fails after resume.

The dead-letter record should point to checkpoint evidence and recommend
`resume_from_checkpoint`, `return_ready`, `create_repair_task`, or
`operator_decision`.

## Integration Points

`agent_loop.py`:

- persist execution and step IDs before launching a handler;
- heartbeat remains lease liveness, not step completion;
- `--resume` should resume from durable checkpoint plus event evidence;
- handler failure should record failed step evidence before release/dead-letter.

`graph/runner.py`:

- include resumable/dead-lettered work in route state;
- avoid recommending a claim when a valid fresh execution owns the task;
- surface ambiguous resume as repair or review, not normal dispatch.

`validate_task_graph.py`:

- continue rejecting cycles and unknown dependencies;
- later add checks that active checkpointed output ownership does not collide
  with active task output ownership.

## Validation Path

Implementation tasks should add tests for:

- duplicate retry of `submit_task` returns one applied result;
- crash after submit but before export resumes at export;
- crash after event append does not append a duplicate event;
- stale started step with conflicting state dead-letters;
- event replay reconstructs the last completed step;
- `--resume` refuses to replay a non-idempotent handler step.
