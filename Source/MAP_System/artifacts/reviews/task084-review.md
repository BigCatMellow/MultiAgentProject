# Review Record: TASK-084

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
CHANGES_REQUESTED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `decide_checkins` is pure and tested: claim suppresses, declaration suppresses, short idle suppresses, 2h+ undeclared idle nudges, renudge throttled | PARTIAL | The listed tests pass, but hcom `blocked` and `waiting` states still nudge if durable status is `available`. That violates the idea-card safety boundary for known blocker/waiting states. |
| 2 | `declare_standby.py` writes SQLite first and exports; `--back` returns agent to available | PASS | Helper updates SQLite and runs the exporter; live state shows `claude-lab-rose` as `standby` / `awaiting_work` in SQLite and `status.json`. |
| 3 | Check-ins are hcom messages only — no `hcom r`, no session spawns | PASS | Check-in path uses `hcom send`, not `hcom r`. `intent=request` is acceptable for this agent-directed check because it asks the agent to answer or declare standby. |
| 4 | Dry-run against live state before restart; suite passes | PASS | `limit_watcher.py --once --dry-run` emitted no check-ins; watcher tests 14/14 and full suite 22/22 pass. |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| No session spawns from the check-in path | NOT BROKEN - no `hcom r` in check-in path. |
| No automatic work assignment in nudge text or behavior | NOT BROKEN - text asks whether there is something to do and offers standby declaration. |
| No nudges to agents with a declared reason, an IN_PROGRESS claim, or non-available durable status | PARTIAL - durable suppression works, but hcom `blocked` / `waiting` state is not suppressed when durable status is still `available`. |
| No direct `status.json` writes | NOT BROKEN - helper writes SQLite first and exports. |

---

## Files Reviewed

- `MAP_System/tasks/TASK-084.json`
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

---

## Findings

| Severity | File | Lines | Finding | Required action |
|---|---|---|---|---|
| REQUIRED | `MAP_System/scripts/limit_watcher.py` | 223-252 | `decide_checkins()` nudges hcom `blocked` and `waiting` sessions when durable status is still `available`. Reproducer: with `process_bound=True`, `status_age_seconds=3h`, durable `available`, and no claim, `decide_checkins()` returns `['rose']` for both `status='blocked'` and `status='waiting'`. The merged IDEA-0007 safety boundary explicitly says not to nudge agents waiting on operator approval or in a known blocker state. | Restrict check-ins to an explicit safe hcom idle state, likely `listening`, or otherwise suppress `blocked` and any approval/waiting statuses. Add regression tests for hcom `blocked` and `waiting`/approval states. |
| REQUIRED | `MAP_System/scripts/limit_watcher.py` | 41, 276, 441-443 | New TASK-084 check-in events are still emitted with `task_id: TASK-083` because the watcher has a single `TASK_ID = "TASK-083"` constant. That misattributes TASK-084 behavior in the durable event log and Monitor. | Attribute check-in path events to TASK-084, either by updating the watcher task id for this version or by using separate task IDs for RnS limit recovery vs declared-idle check-ins. |
| REQUIRED | `MAP_System/tasks/TASK-084.json`; emergence artifacts | `output_paths`; promotion status | TASK-084 created/filled `PROMO-0006`, modified `IDEA-0007`/`IDEA-0008`, rebuilt `emergence/INDEX.md`, and changed `agents/status.json` via `declare_standby.py`, but none of those are in `output_paths`. Also `PROMO-0006` still says `Status: PROPOSED` / `Approved by: PENDING`, and `IDEA-0007` remains `CANDIDATE` even though implementation has been submitted. | Add all substantive durable outputs or document why they are generated/non-owned. If peer review is the approval step, update `PROMO-0006` approval fields and close the source idea lifecycle appropriately before resubmitting, then rebuild the emergence index. |

No BLOCKER findings. REQUIRED findings must be fixed before approval.

---

## Commands Run

- `python3 MAP_System/tests/test_limit_watcher.py`: 14 watcher tests passed.
- `MAP_System/scripts/run_tests.sh`: pass=22 fail=0 total=22.
- `python3 MAP_System/scripts/limit_watcher.py --once --dry-run`: no output, meaning no live false-positive check-ins.
- `python3 MAP_System/scripts/validate_task_graph.py`: passed.
- `python3 MAP_System/scripts/validate_events.py`: errors=0 warnings=33.
- `python3 MAP_System/scripts/map_emergence.py validate`: 22 checked.
- `python3 MAP_System/scripts/map_emergence.py stale`: no findings.
- SQLite/status check: `claude-lab-rose` is `standby` / `awaiting_work` in SQLite and `status.json`; `codex-lab-limo` remains `available`.
- Manual hcom-state reproducer: `decide_checkins()` nudges `listening`, `waiting`, and `blocked` hcom statuses when durable state is `available`; only `active` suppresses.
