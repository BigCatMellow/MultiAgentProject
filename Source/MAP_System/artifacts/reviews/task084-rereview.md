# Review Record: TASK-084 Re-review

## Header

```
task_id:      TASK-084
reviewer:     codex-lab-limo
review_date:  2026-07-02
task_owner:   claude-lab-rose
```

Reviewer (codex-lab-limo) != task owner (claude-lab-rose). Independence check passes.

---

## Verdict

```
APPROVED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `decide_checkins` is pure and tested: claim suppresses, declaration suppresses, short idle suppresses, 2h+ undeclared idle nudges, renudge throttled | PASS | `test_checkin_decision_logic` covers eligible `listening`, short idle, active, dead, claimed, declared, non-available, throttle, and re-nudge cases. |
| 2 | `declare_standby.py` writes SQLite first and exports; `--back` returns agent to available | PASS | Helper writes SQLite then runs exporter; live state shows `claude-lab-rose` as `standby` / `awaiting_work` in SQLite and `status.json`. Code path uses `--back` for `available` / `reason=NULL`. |
| 3 | Check-ins are hcom messages only — no `hcom r`, no session spawns | PASS | Check-in path uses `hcom send --intent request`; no `hcom r` is used in that path. |
| 4 | Dry-run against live state before restart; suite passes | PASS | `limit_watcher.py --once --dry-run` emitted no live check-ins; watcher tests 14/14 and full suite 22/22 pass. |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| No session spawns from the check-in path | NOT BROKEN - check-ins are message-only. |
| No automatic work assignment in nudge text or behavior | NOT BROKEN - text asks whether there is something to do and offers standby declaration. |
| No nudges to agents with a declared reason, an IN_PROGRESS claim, or non-available durable status | NOT BROKEN - all are tested suppression cases. |
| No direct `status.json` writes | NOT BROKEN - `declare_standby.py` writes SQLite first and exports. |

---

## Files Reviewed

- `MAP_System/tasks/TASK-084.json`
- `MAP_System/workflow/task_graph.json`
- `MAP_System/scripts/limit_watcher.py`
- `MAP_System/scripts/declare_standby.py`
- `MAP_System/tests/test_limit_watcher.py`
- `MAP_System/notes/limit-exhaustion-protocol.md`
- `MAP_System/agents/README.md`
- `MAP_System/agents/status.json`
- `MAP_System/agents/limit-watcher-state.json`
- `MAP_System/emergence/ideas/IDEA-0007-declared-idle-checkin-protocol.md`
- `MAP_System/emergence/ideas/IDEA-0008-idle-accountability-heartbeat-for-active-agents.md`
- `MAP_System/emergence/promotions/PROMO-0006-declared-idle-checkin.md`
- `MAP_System/emergence/INDEX.md`
- `MAP_System/events/events.jsonl`

---

## Prior Findings Closure

| Prior finding | Closure |
|---|---|
| hcom `blocked` / `waiting` sessions were check-in eligible | CLOSED - check-ins now require `CHECKIN_SAFE_STATUSES = {"listening"}`; tests pin `blocked` and `waiting` suppression. |
| Check-in events attributed to TASK-083 | CLOSED - `append_event()` accepts `task_id`, and check-in events pass `CHECKIN_TASK_ID = "TASK-084"`. |
| Promotion/idea lifecycle and output paths incomplete | CLOSED - TASK-084 output paths include status and emergence records; IDEA-0007 is `PROMOTED`; PROMO-0006 was approved by this peer review; emergence index rebuilt and validates. |

---

## Risk Identification

| Risk | Severity | Status |
|---|---|---|
| Check-ins can create message noise if hcom status semantics change. | LOW | Mitigated by `listening`-only eligibility, 2h threshold, once-per-window throttle, and message-only behavior. |
| `intent=request` asks agents to respond. | LOW | Acceptable: the operator asked for a "should you be doing something?" nudge, and standby declaration is the desired response when done. |

---

## Commands Run

- `python3 MAP_System/tests/test_limit_watcher.py`: 14 watcher tests passed.
- `MAP_System/scripts/run_tests.sh`: pass=22 fail=0 total=22.
- `python3 MAP_System/scripts/limit_watcher.py --once --dry-run`: no live check-ins emitted.
- `python3 MAP_System/scripts/validate_task_graph.py`: passed.
- `python3 MAP_System/scripts/validate_events.py`: errors=0 warnings=33.
- `python3 MAP_System/scripts/map_emergence.py validate`: 22 checked.
- `python3 MAP_System/scripts/map_emergence.py stale`: no findings.
- SQLite/status check: `claude-lab-rose` is `standby` / `awaiting_work` in SQLite and `status.json`; `codex-lab-limo` remains `available`.
- State sync check: DB, task JSON, and graph all reported `TASK-084` as `SUBMITTED` before approval.
