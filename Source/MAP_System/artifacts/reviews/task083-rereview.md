# Review Record: TASK-083 Re-review

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
APPROVED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Liveness classification uses status + staleness, not list presence; regression test reproduces the overnight incident shape | PASS | `classify_live()` uses hcom status plus `status_age_seconds`; `test_overnight_incident_shape` covers stale-but-listed sessions. |
| 2 | Presumed-down agents get probe-resumes on a capped backoff, cleared when the agent rises | PASS | Incidents are capped by `PROBE_SCHEDULE_MINUTES`; `probe_action()` now anchors retry probes to `reset_nudged_at` after a scheduled-reset nudge, preventing immediate consecutive probes from overdue detection-time slots. |
| 3 | Transcript reset-time extraction used when available, with backoff as fallback, never blocking on it | PASS | `read_transcript_reset()` tail-reads a bounded 64 KiB and falls back to probe scheduling when no reset time is found. |
| 4 | Protocol note updated and branded RnS; suite passes | PASS | `notes/limit-exhaustion-protocol.md` documents Rise & Shine/RnS v2; `run_tests.sh` reports pass=22 fail=0 total=22. |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| No headless resumes | NOT BROKEN - `send_nudge()` uses `hcom r ... --terminal wezterm-tab --go`. |
| No unbounded probe loops | NOT BROKEN - probes remain capped, and retries after known reset are paced from `reset_nudged_at`. |
| No blocking/slow transcript parsing in poll loop | NOT BROKEN - transcript parsing is a bounded tail read. |
| Do not remove v1 recorded `resume_after` behavior | NOT BROKEN - recorded-reset `decide_nudges()` path remains intact. |

---

## Files Reviewed

- `MAP_System/tasks/TASK-083.json`
- `MAP_System/workflow/task_graph.json`
- `MAP_System/scripts/limit_watcher.py`
- `MAP_System/tests/test_limit_watcher.py`
- `MAP_System/notes/limit-exhaustion-protocol.md`
- `MAP_System/agents/limit-watcher-state.json`
- `MAP_System/artifacts/reviews/task083-review.md`

---

## Prior Findings Closure

| Prior finding | Closure |
|---|---|
| Known-reset fallback probes anchored to `detected_at`, allowing extra immediate probes after the scheduled reset nudge | CLOSED - `probe_action()` now uses `reset_nudged_at` when present, and `test_probe_action_with_known_reset` asserts the no-immediate-retry behavior. |
| SQLite/task JSON/task graph status mismatch after submission | CLOSED - DB, task JSON, and task graph all report `SUBMITTED` before approval. |

---

## Risk Identification

| Risk | Severity | Status |
|---|---|---|
| Probe resumes can still spawn visible sessions without a known reset time. | MEDIUM | Accepted for RnS v2 because probes are capped, delayed, visible, and produce BLOCKED give-up events. |
| If `hcom r` fails, the code still records the attempted probe slot as spent. | LOW | Acceptable conservative behavior for a live spawner: it avoids retry storms and leaves event evidence for operator/peer inspection. |

---

## Commands Run

- `python3 MAP_System/tests/test_limit_watcher.py`: 12 watcher tests passed.
- `MAP_System/scripts/run_tests.sh`: pass=22 fail=0 total=22.
- `python3 MAP_System/scripts/validate_task_graph.py`: passed.
- `python3 MAP_System/scripts/validate_events.py`: errors=0 warnings=33.
- `python3 MAP_System/scripts/map_emergence.py stale`: no findings.
- `python3 -c "... TASK-083 ..."`: DB, task JSON, and graph all reported `SUBMITTED`.
- Manual probe-state check: scheduled reset nudge fires at reset time; retry probes wait until the re-anchored `reset_nudged_at` backoff slot.
- Watcher state check: pidfile shows `315816`; `limit-watcher-state.json` mtime advanced after restart and contains no open incidents.
