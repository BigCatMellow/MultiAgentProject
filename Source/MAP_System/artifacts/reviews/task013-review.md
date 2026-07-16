# Review — TASK-013: SQLite Seed Script

**Reviewer:** claude  
**Date:** 2026-06-19  
**Reviewed files:** `migration/schema.sql`, `migration/seed_from_files.py`, `artifacts/tests/sqlite-seed-test.md`  
**Verdict:** APPROVED

---

## Acceptance Criteria

| Criterion | Result |
|-----------|--------|
| Creates `map.db` with all tables from the design document | PASS — all 15 tables present |
| Seeds tasks, dependencies, agents, events, and decisions from current files | PASS — verified against live DB |
| Idempotent: re-running does not duplicate rows | PASS — live re-run showed 0 inserts across all tables |
| Prints a summary of rows inserted or skipped | PASS — summary present and readable |

---

## Verification (live run during review)

```
Seeded /home/home/Downloads/MultiAgentProject/MAP_System/map.db
agents: inserted=0 skipped=42
approval_gate_resume_tasks: inserted=0 skipped=2
approval_gates: inserted=0 skipped=1
artifacts: inserted=0 skipped=4
decisions: inserted=0 skipped=8
events: inserted=0 skipped=25
task_acceptance_criteria: inserted=0 skipped=54
task_dependencies: inserted=0 skipped=3
task_output_paths: inserted=0 skipped=66
tasks: inserted=0 skipped=13
```

DB row counts confirmed:
- agents=6, tasks=13, events=25, decisions=8, artifacts=4, approval_gates=1
- All 13 tasks have correct status and owner
- 50 of 54 acceptance criteria marked met (the 4 unmet are correctly TASK-013's own criteria, which will resolve when the task is marked DONE)
- All 8 decisions parsed from `shared/decisions.md` with correct status values

---

## Findings

| ID | Severity | Finding |
|----|----------|---------|
| R-01 | OPTIONAL | `agents: skipped=42` in the summary is the total number of `ensure_agent` calls (one per event sender, task owner, etc.), not unique agents. Currently 42 calls for 6 distinct agents. Could report unique-agent counts to be less confusing, but the current output is accurate and not misleading once understood. |
| R-02 | OPTIONAL | `command-center` and `langgraph-runner` are seeded as `agent_type='core'` because they appear as event senders but are not in `agents/status.json`. Functionally correct for FK integrity. Could use `agent_type='system'` for clarity when the schema is extended. |
| R-03 | OPTIONAL | DEC-007's status is stored as `"superseded by dec-008"` (the full markdown status line text) instead of the canonical `"superseded"`. Cosmetic artifact of the markdown regex parser — does not affect queries that check for `approved` decisions. Worth normalizing in a future pass. |

No BLOCKER or REQUIRED findings.

---

## Notes

- The dual-path deduplication strategy for events (explicit SELECT before INSERT + `prune_duplicate_events` sweep) is correct given that SQLite UNIQUE constraints treat NULL values as distinct, which would otherwise allow duplicate event rows when `task_id` or `sender_id` is NULL.
- `merged_task()` correctly prefers the individual task JSON file over the task graph entry, which means the DB always reflects the most authoritative task state.
- Schema faithfully implements the design from `artifacts/planning/sqlite-task-board.md` with one useful addition: a `UNIQUE` constraint on `task_acceptance_criteria (task_id, criterion)` that was not in the design doc but prevents duplicate criteria on re-seed.

---

## Verdict

**APPROVED.** Mark TASK-013 DONE.
