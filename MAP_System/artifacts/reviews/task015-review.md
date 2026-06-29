# Review — TASK-015: Runner Reads SQLite

**Reviewer:** claude  
**Date:** 2026-06-19  
**Reviewed files:** `langgraph/runner.py`, `artifacts/tests/runner-sqlite-test.md`  
**Verdict:** APPROVED

---

## Acceptance Criteria

| Criterion | Result |
|-----------|--------|
| Runner loads tasks and agent status from map.db when present | PASS |
| Falls back to JSON files if map.db absent | PASS |
| ready_tasks, blocked_tasks, done_task_ids, available_agents reflect SQLite state | PASS |
| `--record-event` writes to SQLite events table in addition to events.jsonl | PASS |
| Existing `--pretty` output format unchanged | PASS |

---

## Live Verification

**SQLite read path:**
```
source: loaded tasks from map.db, loaded agents from map.db
available_agents: [claude, codex]
unavailable_agents: [antigravity, gemini]
route: review  (TASK-015 is SUBMITTED)
```
System agents (`command-center`, `langgraph-runner`) correctly excluded from available/unavailable lists via `is_assignable_agent()`.

**JSON fallback** (map.db moved aside):
```
loaded /…/workflow/task_graph.json
loaded agents/status.json
PASS: JSON fallback fires correctly
```

**`--record-event` dual write:**
```
SQLite events: 32 → 33
JSONL lines:   32 → 33
latest event: ('PROGRESS', 'langgraph-runner', 'Routed workflow to review: …')
```
Both stores updated atomically in the same run.

---

## Findings

| ID | Severity | Finding |
|----|----------|---------|
| R-01 | OPTIONAL | `route_claim_or_assign` command hint still says "Update the task owner/status in MAP_System/tasks/ and workflow/task_graph.json" — now that SQLite is the claim coordinator, the hint could reference `db/claims.py`. Low priority since it is informational text only. |
| R-02 | OPTIONAL | `state_source` ("sqlite" or "json") is computed internally but not exposed in `--pretty` output. Useful for debugging; could be added to `summarize()` if desired. |

No BLOCKER or REQUIRED findings.

---

## Notes

- `load_agents_from_sqlite` queries all agent fields and returns a dict keyed by `agent_id`, matching the shape the rest of the runner expects from the JSON path. No behavioral change to downstream routing logic.
- `append_sqlite_event` correctly upserts the `langgraph-runner` agent row before inserting the event, so the foreign key on `sender_id` is always satisfied.
- The `is_assignable_agent` guard excludes both `agent_type == "system"` agents and the hardcoded `command-center` / `langgraph-runner` IDs — belt-and-suspenders approach that handles agents seeded before the `system` type was defined.

---

## Verdict

**APPROVED.** Mark TASK-015 DONE.
