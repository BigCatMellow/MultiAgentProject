# Agent Loop Test

Task: TASK-021  
Tester: codex  
Date: 2026-06-19

## Commands

```bash
python3 -m py_compile MAP_System/scripts/agent_loop.py
python3 MAP_System/scripts/agent_loop.py --once --dry-run
MAP_System/.venv/bin/python MAP_System/scripts/agent_loop.py --once --dry-run
MAP_System/.venv/bin/python -c "from MAP_System.scripts.agent_loop import Config, choose_after_claim; from pathlib import Path; c=Config('codex', Path('MAP_System/map.db'), False, False, None, 1, 10, True, 0, 300); print(choose_after_claim({'last_result':'claim_failed','iterations':1}, c)); print(choose_after_claim({'last_result':'no_ready_task','iterations':1}, c)); c2=Config('codex', Path('MAP_System/map.db'), True, False, None, 1, 10, True, 1, 300); print(choose_after_claim({'last_result':'claim_failed','iterations':1}, c2));"
```

Temp-DB behavior tests used `MAP_System/migration/schema.sql` and imported `MAP_System/scripts/agent_loop.py` under the project venv.

## Results

### Idle Poll

```text
reconciled=none
route=wait_or_reconcile
```

Works from both system `python3` and `MAP_System/.venv/bin/python`; the script re-execs into the venv when needed.

### Claim, Heartbeat, Submit, Export

Fixture: `TASK-LOOP-1` in `READY`.

```text
reconciled=none
route=claim_or_assign
claimed task_id=TASK-LOOP-1
heartbeat task_id=TASK-LOOP-1
heartbeat task_id=TASK-LOOP-1
submitted task_id=TASK-LOOP-1
exported state
('SUBMITTED', None, None, None, 2)
exports 1
```

Verified claim through `db/claims.py`, heartbeat during handler execution, submit on success, and export callback after submit.

### Dry-Run Claim Route

Fixture: runner surfaced a ready task, loop ran with `dry_run=True`.

```text
reconciled=none
route=claim_or_assign
dry_run: would_claim task_id=TASK-LOOP-DRY
('READY', None, 1)
```

Verified dry-run reports the claim target without mutating task status, claimant, or attempt count.

### Claim Race

Fixture: runner surfaced a task already claimed by `claude`.

```text
reconciled=none
route=claim_or_assign
claim_failed task_id=TASK-LOOP-RACE
('IN_PROGRESS', 'claude')
```

Verified failed claim does not mutate the existing claim.

Post-review route regression:

```text
reconcile
reconcile
end
```

Verified daemon mode routes `claim_failed` and `no_ready_task` back to `reconcile`, while `--once` still exits.

### Operator Interrupt

Current project route is `review`, so dry-run reaches the operator interrupt path:

```text
reconciled=none
route=review
{"interrupted":true,"message":"operator input required for route=review"}
```

Verified `run_loop()` surfaces interrupt state instead of exiting silently.

### Handler Failure Release

Fixture: handler exited non-zero.

```text
reconciled=none
route=claim_or_assign
claimed task_id=TASK-LOOP-FAIL
released task_id=TASK-LOOP-FAIL status=READY reason=CalledProcessError
('READY', None, None, None)
```

Verified failed handler releases the claim back to `READY`.

### Shutdown Release

Fixture: a claimed task was running a long handler while `SHUTDOWN.requested` was set.

```text
heartbeat task_id=TASK-LOOP-SHUT
heartbeat task_id=TASK-LOOP-SHUT
released task_id=TASK-LOOP-SHUT status=READY reason=KeyboardInterrupt
['KeyboardInterrupt']
('READY', None, None, None)
```

Verified shutdown terminates the handler and releases the task.

## Notes

- The loop is a cyclic LangGraph `StateGraph`: `reconcile -> poll -> claim -> submit -> reconcile`.
- It uses `MapSqliteSaver` as the checkpointer.
- Routes that need operator action (`review`, `propose_helper`) call `interrupt()`.
- The loop does not auto-spawn helpers and does not bypass approval gates.
