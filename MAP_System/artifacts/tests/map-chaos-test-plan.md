# MAP Chaos Test Plan (TASK-155, Wave 7)

Status: draft-active
Owner: command-center
Built by: TASK-155

## Purpose

This plan defines focused chaos probes for MAP resilience controls. The goal
is not to make failure impossible; it is to prove detection, containment,
resume, and repair paths work without corrupting canonical state.

This is a test design artifact. TASK-155 does not implement the probes.

## Test Principles

- Inject one fault at a time before combining faults.
- Assert containment scope, not just eventual success.
- Verify canonical state with validators after each probe.
- Check idempotency by looking for duplicate effects, not just return codes.
- Test circuit breakers under persistent failure, not only random failure.
- Keep destructive or poisoned-state probes in isolated temp copies until a
  rollback/reconcile path exists.

Minimum post-probe validators:

- `MAP_System/scripts/validate_task_graph.py`
- `MAP_System/scripts/validate_task_mirrors.py --root MAP_System`
- `MAP_System/scripts/validate_events.py --fail-on-new`
- any probe-specific dead-letter/checkpoint validator added later

## Probe 1: Killed Agent-Loop Handler

Fault:

- Start `scripts/agent_loop.py` with a handler that writes a checkpoint, then
  kill the handler process before submit/export.

Expected detection:

- lease heartbeat eventually becomes stale or handler exits nonzero;
- task is released, reclaimed, or dead-lettered according to retry policy;
- no terminal task transition is recorded without submit evidence.

Expected containment:

- task returns to `READY` or enters dead-letter queue;
- no duplicate submission event appears on retry;
- file mirrors remain valid after export/reconcile.

Pass criteria:

- one recoverable dead-letter or retry record exists;
- rerun resumes at the first incomplete durable step;
- idempotency registry shows duplicate write suppression where applicable.

## Probe 2: Stale Mirror

Fault:

- Make SQLite task state and exported task JSON disagree in an isolated copy,
  or interrupt export after DB update but before mirror write.

Expected detection:

- mirror validator reports drift;
- self-repair classification is `DRIFT` or `BLOCKING` depending on whether
  dispatch is blocked.

Expected containment:

- canonical DB remains preferred only if validator evidence indicates mirror
  drift rather than DB corruption;
- mechanical re-export repairs the mirror and records a Repair Record when
  severity is DRIFT or higher.

Pass criteria:

- `validate_task_mirrors.py` fails before repair and passes after repair;
- `validate_task_graph.py` passes after export;
- no unrelated task output paths are changed.

## Probe 3: Malformed Protocol Output

Fault:

- Feed a malformed hcom/protocol packet or malformed helper output into a
  bounded intake/review path.

Expected detection:

- protocol validator rejects the packet;
- semantic validator or reviewer path refuses to treat it as approved output;
- repeated malformed output increments circuit-breaker input for the source.

Expected containment:

- malformed output is quarantined as draft/invalid;
- no task is submitted, approved, or released from malformed content alone;
- helper/local lane can be paused without halting unrelated core work.

Pass criteria:

- validator error identifies the malformed field or missing requirement;
- runner continues unrelated work;
- repeated failures produce a scoped breaker signal.

## Probe 4: Hung Agent And Reaper

Fault:

- Simulate an agent that owns an `IN_PROGRESS` task but stops heartbeating and
  does not respond to a nudge.

Expected detection:

- liveness state moves from `working` to `suspect`;
- reaper nudges once, then reclaims or dead-letters after timeout;
- repeated incidents mark the agent `broken` or paused.

Expected containment:

- only the affected task/agent is paused;
- task ownership is cleared through sanctioned DB helpers;
- exports and mirror validation run after mutation.

Pass criteria:

- stale lease is not left indefinitely active;
- task is recoverable through READY or dead-letter replay;
- failure circuit breaker suppresses new work to the sick agent after the
  configured threshold.

## Probe 5: Mid-Task Resume

Fault:

- Stop a durable execution after one or more checkpointed steps but before
  completion.

Expected detection:

- resume reads checkpoint, task row, event log, and idempotency registry;
- completed steps are skipped;
- first incomplete safe step resumes.

Expected containment:

- no duplicate event append;
- no duplicate task submit;
- stale export cannot overwrite newer canonical state.

Pass criteria:

- resumed run reaches the same final state as an uninterrupted run;
- idempotency registry marks duplicate retries as ignored/skipped;
- validators pass after resume.

## Probe 6: Committed Poisoned-State Recovery

Fault:

- In an isolated copy, commit a plausible but wrong state change such as a bad
  dependency edge, incorrect output path, or invalid task status transition.

Expected detection:

- validator, review, or downstream failure identifies the poisoned state;
- self-repair severity is classified based on blast radius and authority;
- affected outputs/tasks are quarantined.

Expected containment:

- downstream tasks that depend on poisoned outputs are blocked;
- unrelated tasks can continue;
- structural fixes are proposed, not silently applied.

Pass criteria:

- repair record documents what was found, severity, fix, and verification;
- validator fails before correction and passes after approved/mechanical fix;
- dependency DAG identifies downstream tasks requiring revalidation.

## Combined Stress Scenario

After individual probes pass, run a bounded combined scenario:

- one handler crash;
- one stale mirror;
- one malformed helper output;
- one persistently failing agent.

Expected result:

- no lost task;
- no duplicate canonical write;
- no cascade beyond declared dependency/quarantine scope;
- circuit breaker pauses only the persistently failing agent/lane;
- operator request is generated only for structural or global decisions.

## Metrics

Record:

- task success rate;
- lost tasks;
- cascade failures;
- double-applied writes;
- dead-letter count and replay closure rate;
- breaker false positives/false negatives;
- time to detection and time to recovery;
- validators passing after recovery.

Round 4 simulation suggests success rate alone is insufficient: idempotency
failures may appear only as double-applies, and circuit breakers must be
tested against persistent failure to show their value.
