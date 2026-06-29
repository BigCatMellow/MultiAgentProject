# Reconcile Script Test

Task: TASK-017
Tester: codex
Date: 2026-06-19

## Commands

```bash
python3 -m py_compile MAP_System/scripts/reconcile.py
python3 MAP_System/scripts/reconcile.py
python3 -c "backup map.db and events.jsonl; insert expired fixture; run reconcile.py; verify; restore backups"
```

## No-Op Run

```text
expired_count=0
expired_task_ids=none
```

The no-op run appended a `PROGRESS` event to `MAP_System/events/events.jsonl` and inserted the same event into SQLite.

## Expired-Lease Run

The fixture test used a temporary replacement `MAP_System/map.db` and restored the real database and event log afterward.

```text
expired_count=1
expired_task_ids=TASK-X-EXPIRE
('READY', None, None)
Expired stale task leases: count=1; task_ids=TASK-X-EXPIRE.
```

Verified:

- `expire_leases()` returned the expired task ID.
- The task moved from `IN_PROGRESS` to `READY`.
- `claimed_by`, `lease_expires_at`, and `heartbeat_at` were cleared.
- The script logged the summary to SQLite events and JSONL.
- `python3 MAP_System/scripts/reconcile.py` exits cleanly when nothing is expired.
