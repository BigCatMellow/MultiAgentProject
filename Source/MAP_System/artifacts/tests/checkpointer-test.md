# Checkpointer + Interrupt Test

Task: TASK-022  
Tester: claude  
Date: 2026-06-19

## Files

- `MAP_System/db/checkpointer.py` — `MapSqliteSaver` backed by `map.db`
- `MAP_System/langgraph/runner.py` — upgraded with `check_approval_gates` node, `--thread-id`, `--approve`, `--reject`

## Tests Run

### 1. No regression (no --thread-id)
```bash
MAP_System/.venv/bin/python MAP_System/langgraph/runner.py --pretty
```
Result: `route: wait_or_reconcile | done: 20` — identical to pre-TASK-022 behavior.

### 2. Checkpointed run, no pending gates
```bash
MAP_System/.venv/bin/python MAP_System/langgraph/runner.py --thread-id test-ck1 --pretty
```
Result: completes normally, `interrupted: false`.

### 3. Interrupt at approval gate
Inserted synthetic `GATE-TEST2` with `status='pending'` into `approval_gates`.
```bash
MAP_System/.venv/bin/python MAP_System/langgraph/runner.py --thread-id gt2 --pretty
```
Result:
```json
{
  "interrupted": true,
  "thread_id": "gt2",
  "gate": {"gate_id": "GATE-TEST2", "name": "Release Gate", ...},
  "resume_hint": "langgraph-run --approve gt2  # to approve\nlanggraph-run --reject gt2   # to reject"
}
```

### 4. Resume with --approve
```bash
MAP_System/.venv/bin/python MAP_System/langgraph/runner.py --approve gt2 --pretty
```
Result: `{"resumed": true, "decision": "approved", ...}` — graph completed.
SQLite: `approval_gates.status = 'approved'` for `GATE-TEST2`.

### 5. MapSqliteSaver unit test
Isolated `StateGraph` with `interrupt()` in a gate node, backed by a temp DB:
- First `invoke()`: surfaces `__interrupt__` with gate details
- `app.invoke(Command(resume=True), cfg)`: resumes, `approved=True`, `value="after_interrupt"`
- Checkpoint tables (`lg_checkpoints`, `lg_checkpoint_writes`) created in `map.db`

### 6. Reject via --reject
Inserted synthetic `GATE-REJECT-01` with `status='pending'`.
```bash
MAP_System/.venv/bin/python MAP_System/langgraph/runner.py --thread-id gr1 --pretty
MAP_System/.venv/bin/python MAP_System/langgraph/runner.py --reject gr1 --pretty
```
Result: `{"resumed": true, "decision": "rejected", ...}`.
SQLite: `approval_gates.status = 'rejected'` for `GATE-REJECT-01`.

**Fix (R-01 from code review):** `check_approval_gates` used `if decision and ...`, which short-circuits on `False`.
Changed to `if decision is not None and ...` so rejections are also persisted.

## Notes

- Without `--thread-id`, behavior is identical to pre-TASK-022 (no checkpointer attached, `check_approval_gates` node runs but `interrupt()` is a no-op without a checkpointer — it completes silently).
- `sys.path.insert` in `main()` scoped to the checkpointer import only; does not affect module-level imports.
