# Review Record: TASK-083

## Header

```
task_id:      TASK-083
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
| 1 | Liveness classification uses status + staleness, not list presence; regression test reproduces the overnight incident shape | PASS | `classify_live()` uses hcom status + `status_age_seconds`; `test_overnight_incident_shape` covers stale-but-listed sessions. |
| 2 | Presumed-down agents get probe-resumes on a capped backoff, cleared when the agent rises | PARTIAL | Incidents and cap exist, but the known-reset retry path can collapse earlier backoff slots into immediate repeated probes after the scheduled reset nudge. |
| 3 | Transcript reset-time extraction used when available, with backoff as fallback, never blocking on it | PASS | `read_transcript_reset()` tail-reads 64 KiB and falls back to probing when no reset time is found. |
| 4 | Protocol note updated and branded RnS; suite passes | PASS | Protocol note documents Rise & Shine/RnS v2; `run_tests.sh` reports pass=22 fail=0 total=22. |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| No headless resumes | NOT BROKEN - `send_nudge()` uses `hcom r ... --terminal wezterm-tab --go`. |
| No unbounded probe loops | NEEDS FIX - total probes are capped, but known-reset fallback can emit several probes on consecutive polls because overdue slots are anchored to detection time. |
| No blocking/slow transcript parsing in poll loop | NOT BROKEN - transcript read is a bounded tail read. |
| Do not remove v1 recorded `resume_after` behavior | NOT BROKEN - `decide_nudges()` path remains. |

---

## Files Reviewed

- `MAP_System/tasks/TASK-083.json`
- `MAP_System/scripts/limit_watcher.py`
- `MAP_System/tests/test_limit_watcher.py`
- `MAP_System/notes/limit-exhaustion-protocol.md`
- `MAP_System/agents/limit-watcher-state.json`
- `MAP_System/workflow/task_graph.json`

---

## Findings

| Severity | File | Lines | Finding | Required action |
|---|---|---|---|---|
| REQUIRED | `MAP_System/scripts/limit_watcher.py` | 187-204, 335-345 | After a known `reset_at` nudge is sent, `probe_action()` falls through to the probe schedule while still anchoring probe due times to `detected_at`. If detection was hours before reset, the 15/45/90/150/240 minute slots are already overdue, so subsequent 60s polls can send multiple extra `hcom r` probes immediately after the scheduled-reset nudge. This violates the capped-backoff intent for a live session spawner. The current test at `test_limit_watcher.py:162-172` locks in that bad behavior by expecting an immediate retry two minutes after reset. | Re-anchor retry probes after a known-reset nudge to the reset nudge time, record `last_nudged_at`, or treat the scheduled reset nudge as the first probe slot. Add a regression asserting no immediate consecutive probes after a successful scheduled-reset nudge. |
| REQUIRED | `MAP_System/tasks/TASK-083.json` / `MAP_System/workflow/task_graph.json` | status field | SQLite has TASK-083 as `SUBMITTED`, but the exported task JSON and task graph still say `READY`. That leaves file-backed MAP state out of sync with the DB immediately after submission. | Re-export/sync the task mirrors so JSON, graph, and SQLite all reflect the same state after rework/submission. |

No BLOCKER findings. REQUIRED findings must be fixed before approval.

---

## Commands Run

- `python3 MAP_System/tests/test_limit_watcher.py`: 12 watcher tests passed.
- `MAP_System/scripts/run_tests.sh`: pass=22 fail=0 total=22.
- `python3 MAP_System/scripts/validate_task_graph.py`: passed.
- `python3 MAP_System/scripts/validate_events.py`: errors=0 warnings=33.
- `python3 MAP_System/scripts/map_emergence.py stale`: no findings.
- `python3 -c "import sqlite3; ... TASK-083 ..."`: SQLite status `SUBMITTED`.
- `python3 -c "import json; ... TASK-083 ..."`: task JSON and graph status `READY`.
- Manual probe-state reproduction: after a scheduled reset nudge at 5h+1m, subsequent minute polls returned `nudge` repeatedly for earlier overdue probe slots.
