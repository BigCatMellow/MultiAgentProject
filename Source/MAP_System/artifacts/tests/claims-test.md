# SQLite Claims Test

Task: TASK-014  
Tester: codex  
Date: 2026-06-19

## Commands

```bash
python3 -m py_compile MAP_System/db/claims.py
python3 -c "import sqlite3, tempfile; from pathlib import Path; from MAP_System.db.claims import claim_task, heartbeat, submit_task, release_task, expire_leases; ..."
```

The behavior test created a temporary SQLite database from `MAP_System/migration/schema.sql`, inserted two agents and three synthetic tasks, and removed the database after assertions completed.

## Result

```text
[('TASK-A', 'SUBMITTED', None, None, None, 2), ('TASK-B', 'READY', None, None, None, 3), ('TASK-C', 'READY', None, None, None, 2)]
claims behavior ok
```

Verified behavior:

- `claim_task()` returns `True` for a READY task and increments `attempt`.
- A second claim on the same in-progress task returns `False`.
- `claim_task()` returns `False` when `attempt >= max_attempts`.
- `claim_task()` can reclaim an expired in-progress task.
- `heartbeat()` extends the lease only for the current claimant.
- `submit_task()` sets status to `SUBMITTED` and clears claim and lease fields.
- `release_task()` returns `False` after the task is no longer claimed.
- `expire_leases()` returns expired in-progress tasks to `READY` and clears claim and lease fields.
