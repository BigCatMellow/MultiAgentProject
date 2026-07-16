# Review — TASK-017 + TASK-018: Reconcile Script + SQLite Export

**Reviewer:** claude  
**Date:** 2026-06-19  
**Reviewed files:** `scripts/reconcile.py`, `migration/export_to_files.py`, `artifacts/tests/reconcile-test.md`, `artifacts/tests/export-test.md`  
**Verdict:** APPROVED (both)

---

## TASK-017 — Reconciliation Script

### Acceptance Criteria

| Criterion | Result |
|-----------|--------|
| `expire_leases()` result logged to events.jsonl | PASS |
| `expire_leases()` result logged to SQLite events table | PASS |
| Prints count and task IDs | PASS |
| No-op run exits cleanly with zero count | PASS |
| Runnable as `python3 MAP_System/scripts/reconcile.py` | PASS |

### Live Verification

**No-op run:**
```
expired_count=0
expired_task_ids=none
SQLite event: ('PROGRESS', 'reconcile', 'Expired stale task leases: count=0; task_ids=none.')
JSONL: reconcile  Expired stale task leases: count=0; task_ids=none.
```

**Expired-lease fixture:**
```
expired_count=1
expired_task_ids=TEST-EXPIRE
task state: ('READY', None)
PASS: expired task returned to READY
```

### Findings

| ID | Severity | Finding |
|----|----------|---------|
| R-01 | OPTIONAL | `reconcile` agent is inserted with `agent_type='system'` via `ON CONFLICT DO UPDATE` — correct, and consistent with other system senders. |

No BLOCKER or REQUIRED findings.

---

## TASK-018 — SQLite-to-JSON Export

### Acceptance Criteria

| Criterion | Result |
|-----------|--------|
| Reads tasks from map.db, writes/updates `tasks/TASK-NNN.json` | PASS |
| Updates status and owner in `workflow/task_graph.json` | PASS |
| Rewrites `agents/status.json` from agents table | PASS |
| Idempotent: re-running produces no diff when already in sync | PASS |
| Prints summary of files written vs unchanged | PASS |

### Live Verification

```
dry_run:  files_written=0  files_unchanged=22   ← already in sync
real run: files_written=0  files_unchanged=22   ← idempotent confirmed

agents/status.json: [antigravity, claude, codex, gemini]   ← system agents excluded
available_agents in runner: [claude, codex]                 ← correct
```

### Findings

| ID | Severity | Finding |
|----|----------|---------|
| R-02 | RECOMMENDED | `existing_agent_note()` re-reads `agents/status.json` once per agent during export. For 4 agents this is negligible, but if the agent count grows it becomes O(n) file reads. Caching the read outside the loop would fix it with one line. Not blocking. |
| R-03 | OPTIONAL | `graph_payload()` hardcodes the fallback `project_id` as `"MAP-BOOTSTRAP-20260617"`. If a second project is ever added, this default would be wrong. Low risk while MAP_System hosts one project. |

No BLOCKER or REQUIRED findings.

---

## Cross-Cutting Notes

- System agent filtering is consistent across all three scripts (`seed_from_files.py`, `export_to_files.py`, `reconcile.py`) and the runner's `is_assignable_agent()`. The `SYSTEM_AGENTS` constant in `export_to_files.py` handles agents seeded before `agent_type='system'` was established.
- `export_to_files.py` preserves `input_paths` from the existing task file (SQLite does not store that field). Correct — no data loss.

---

## Verdict

**APPROVED.** Mark TASK-017 and TASK-018 DONE.
