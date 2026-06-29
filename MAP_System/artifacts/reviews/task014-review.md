# Review — TASK-014: SQLite Claim Module

**Reviewer:** claude  
**Date:** 2026-06-19  
**Reviewed files:** `db/__init__.py`, `db/claims.py`, `artifacts/tests/claims-test.md`  
**Verdict:** APPROVED

---

## Acceptance Criteria

| Criterion | Result |
|-----------|--------|
| `claim_task()` returns True only when rowcount==1; False if already claimed or max_attempts exceeded | PASS |
| `heartbeat()` extends lease_expires_at and updates heartbeat_at for claimant only | PASS |
| `release_task()` sets status to SUBMITTED and clears claimed_by and lease fields | PASS |
| `expire_leases()` returns expired tasks to READY | PASS |
| All functions accept db_path, default to map.db | PASS |
| Test documented in artifacts/tests/claims-test.md | PASS |

---

## Live Verification

Seven independent checks run against a fresh temp DB during review:

| Check | Result |
|-------|--------|
| `claim_task()` sets IN_PROGRESS, increments attempt, returns True | PASS |
| Double-claim returns False (task still IN_PROGRESS) | PASS |
| `heartbeat()` succeeds for claimant, fails for non-claimant | PASS |
| `release_task()` with wrong agent returns False | PASS |
| `submit_task()` sets SUBMITTED, clears claimed_by / lease_expires_at / heartbeat_at | PASS |
| `claim_task()` returns False when attempt == max_attempts | PASS |
| `expire_leases()` returns task with past lease_expires_at to READY, clears claim fields | PASS |

---

## Findings

| ID | Severity | Finding |
|----|----------|---------|
| R-01 | OPTIONAL | `expire_leases()` uses `executemany` in a loop over already-fetched task IDs. For the expected scale (handful of tasks), this is fine. At larger scale a single `UPDATE ... WHERE task_id IN (...)` would be more efficient, but that is a future optimization. |
| R-02 | OPTIONAL | `connect()` is a public export but is not listed in `db/__init__.py`. If downstream code imports it directly it will still work, but making the public surface explicit would help. Low priority. |

No BLOCKER or REQUIRED findings.

---

## Notes

- The `_lease_modifier()` helper correctly validates `lease_seconds > 0` before constructing the SQLite datetime modifier string, preventing a silent no-op or negative lease.
- `release_task()` correctly guards on `status = 'IN_PROGRESS'` in the WHERE clause, so calling it after `submit_task()` safely returns False rather than double-mutating state.
- `expire_leases()` fetches task IDs before updating, which is the correct pattern — avoids updating rows that were legitimately reclaimed between the SELECT and UPDATE in multi-writer scenarios (SQLite serializes writes, so this is safe here regardless).

---

## Verdict

**APPROVED.** Mark TASK-014 DONE. TASK-015 and TASK-016 are now unblocked.
