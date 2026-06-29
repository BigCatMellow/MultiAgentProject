# Autonomous Claim Loop Protocol

**Author:** claude  
**Date:** 2026-06-19  
**Status:** Draft — spec for TASK-021 implementation  
**Depends on:** `db/claims.py` (TASK-014), `langgraph/runner.py` (TASK-015), `scripts/reconcile.py` (TASK-017)

---

## Purpose

Define how an agent process polls the LangGraph runner, auto-claims the next ready task, works on it, sends heartbeats, and submits — without human intervention between tasks. This protocol is the spec for `scripts/agent-loop.py` (TASK-021).

---

## Loop Invariants

1. An agent claims at most one task at a time.
2. An agent never abandons a claimed task mid-work. On shutdown, it finishes the current task or releases it explicitly.
3. The runner is authoritative on what is ready. The loop never claims a task the runner does not surface.
4. Heartbeats are the only way to hold a lease. Silence = expiry.

---

## The Cycle

```
START
  │
  ▼
poll_runner()
  │
  ├─ route == wait_or_reconcile ──► sleep(POLL_INTERVAL) ──► poll_runner()
  │
  ├─ route == wait_for_agent ─────► sleep(POLL_INTERVAL) ──► poll_runner()
  │
  ├─ route == review ─────────────► skip (reviewer handles separately) ──► sleep ──► poll_runner()
  │
  └─ route == claim_or_assign ────► try_claim()
       │
       ├─ claim failed (race) ─────► sleep(BACKOFF) ──► poll_runner()
       │
       └─ claim succeeded ─────────► do_work()
              │
              ├─ [every HEARTBEAT_INTERVAL seconds] ──► heartbeat()
              │
              └─ work complete ────► submit_task() ──► poll_runner()

SHUTDOWN SIGNAL received at any point:
  ├─ if no active claim ──────────► exit cleanly
  └─ if claim held ───────────────► finish_or_release() ──► exit
```

---

## Decision Points

### poll_runner()

Call `langgraph-run --pretty` (subprocess) or import and invoke `runner.build_graph()` directly. Extract `next_route` and `ready_tasks`.

**Skip `propose_helper` route** — helper spawning requires operator approval; the loop does not auto-spawn helpers.

### try_claim()

```python
task_id = ready_tasks[0]   # runner already sorted by priority
success = claim_task(task_id, agent_id, lease_seconds=LEASE_SECONDS)
```

On `success=False`: another agent claimed it first (race). Sleep `BACKOFF_SECONDS` and re-poll. Do not retry the same task immediately — the runner will surface the next ready one.

On `success=True`: record claim in local state. Begin `do_work()`.

### do_work()

The loop calls the agent's task handler with the task record. The handler is agent-specific (Codex implements, Claude reviews). The loop's job is the control plane only — it does not perform the task itself.

The task handler must:
- accept `task_id` and `db_path`
- return when done (not loop internally beyond its own retry logic)
- raise on unrecoverable error

### heartbeat()

Run in a background thread or via periodic check inside the work loop:

```python
while working:
    time.sleep(HEARTBEAT_INTERVAL)
    ok = heartbeat(task_id, agent_id, lease_seconds=LEASE_SECONDS)
    if not ok:
        # lease was stolen or task was reset — stop work, do not submit
        raise LeaseRevoked(task_id)
```

`HEARTBEAT_INTERVAL` must be significantly less than `LEASE_SECONDS` (rule of thumb: ≤ 1/3 of lease). With the current 1800s lease, heartbeat every 300–600s.

### submit_task()

```python
submit_task(task_id, agent_id)
# then sync files from SQLite
export_to_files()   # from migration/export_to_files.py (TASK-018)
```

After submission, re-poll immediately (no sleep).

### finish_or_release() on shutdown

```python
if current_task:
    if work_is_completable_quickly():
        finish → submit_task()
    else:
        release_task(task_id, agent_id, status="READY")
        log("released task back to READY on shutdown")
```

Never leave a task in `IN_PROGRESS` with an active claim on shutdown. Either submit or release.

---

## Failure Modes

| Failure | Behavior |
|---------|----------|
| Claim race (lost to another agent) | Sleep BACKOFF, re-poll. Do not retry same task. |
| `heartbeat()` returns False (lease stolen or expired externally) | Raise `LeaseRevoked`, abandon work, re-poll. |
| `max_attempts` exhausted | Runner will not surface the task again. Log warning. Move on. |
| `do_work()` raises unrecoverable error | `release_task(..., status="BLOCKED")`, log error, re-poll. |
| `submit_task()` returns False | Task was already released externally. Log warning, re-poll. |
| Runner produces no ready tasks for N consecutive polls | Increase poll interval (exponential backoff up to MAX_POLL_INTERVAL). |

---

## Configuration

```yaml
# In workflow/runtime_policy.yaml or agent-loop config block
agent_loop:
  poll_interval_seconds: 30          # time between runner polls when idle
  max_poll_interval_seconds: 300     # cap for exponential backoff
  backoff_seconds: 10                # sleep after a failed claim before re-polling
  heartbeat_interval_seconds: 300    # how often to renew the lease while working
  lease_seconds: 1800                # must match runtime_policy task_lease_seconds
  reconcile_on_startup: true         # call expire_leases() once at start
  export_after_submit: true          # call export_to_files() after each submit
```

---

## Interaction with reconcile.py

On startup, the loop calls `expire_leases()` once (if `reconcile_on_startup: true`). This returns any abandoned tasks from a previous session to READY before the loop begins polling. The reconcile script can also run independently on a cron for safety.

---

## Pseudocode

```python
def run_loop(agent_id, db_path, config):
    if config.reconcile_on_startup:
        expired = expire_leases(db_path=db_path)
        log(f"reconciled: {expired}")

    poll_interval = config.poll_interval_seconds
    current_task = None

    while not shutdown_requested():
        state = run_runner(db_path)
        route = state["next_route"]

        if route in ("wait_or_reconcile", "wait_for_agent"):
            sleep(poll_interval := min(poll_interval * 1.5, config.max_poll_interval_seconds))
            continue

        if route == "claim_or_assign":
            poll_interval = config.poll_interval_seconds   # reset backoff
            task_id = state["ready_tasks"][0]
            if not claim_task(task_id, agent_id, lease_seconds=config.lease_seconds, db_path=db_path):
                sleep(config.backoff_seconds)
                continue

            current_task = task_id
            try:
                do_work_with_heartbeat(task_id, agent_id, config, db_path)
                submit_task(task_id, agent_id, db_path=db_path)
                if config.export_after_submit:
                    export_to_files(db_path=db_path)
            except LeaseRevoked:
                log(f"lease revoked for {task_id}, re-polling")
            except UnrecoverableError as e:
                release_task(task_id, agent_id, status="BLOCKED", db_path=db_path)
                log(f"blocked {task_id}: {e}")
            finally:
                current_task = None
            continue

        sleep(config.poll_interval_seconds)

    # Shutdown
    if current_task:
        release_task(current_task, agent_id, status="READY", db_path=db_path)
```

---

## Output Paths for TASK-021

The implementation should produce:
- `MAP_System/scripts/agent_loop.py` — the loop itself
- `MAP_System/artifacts/tests/agent-loop-test.md` — test covering: idle poll, successful claim, claim race, heartbeat renewal, shutdown release

---

## Open Questions (for TASK-021 implementer)

- Should `do_work()` be a plugin function passed in, or should the loop exec a subprocess per task type? Subprocess is safer (crash isolation); plugin is faster (no startup cost). Recommend subprocess for now.
- Should the loop write its own PID file to prevent duplicate instances on the same agent?
