# Review Record: TASK-080

## Header

```
task_id:      TASK-080
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
| 1 | Watcher nudges an agent at most once per resume_after window (no spawn loops) | PASS | `decide_nudges()` skips when `state["nudged"][agent] == resume_after`; `test_one_nudge_per_window` covers same-window suppression and a new window. |
| 2 | All resumes use --terminal wezterm-tab, never headless, per operator visibility rule | PASS | `send_nudge()` constructs `hcom r <agent> --terminal wezterm-tab --go --hcom-prompt ...`; no `--headless` path found. |
| 3 | Unparseable resume_after values are skipped with a durable warning, not guessed | PASS | Existing live event flags antigravity's free-text `resume_after`; `test_unparseable_reported_once` verifies one warning per exact value. |
| 4 | Silent stops (agent gone from hcom without status.json update) produce a durable event | PASS | `hcom_live_agents()` now returns `[]` for successful empty output and `None` only for genuine hcom failure; `test_empty_hcom_list_is_data_not_failure` covers the all-vanished case. |
| 5 | Test registered in run_tests.sh and full suite passes | PASS | `run_tests.sh` includes `limit_watcher_test`; full suite passes `pass=19 fail=0 total=19`. |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Headless agent spawning | NOT BROKEN |
| LLM/Ollama inference in polling loop | NOT BROKEN |
| Watcher writes other agents' status entries | NOT BROKEN |
| Automatic retry storms | NOT BROKEN |

---

## Files Reviewed

- `MAP_System/scripts/limit_watcher.py`
- `MAP_System/scripts/start-limit-watcher.sh`
- `MAP_System/tests/test_limit_watcher.py`
- `MAP_System/notes/limit-exhaustion-protocol.md`
- `MAP_System/agents/status.json`
- `MAP_System/agents/limit-watcher-state.json`
- `MAP_System/scripts/run_tests.sh`
- `MAP_System/events/events.jsonl`
- `MAP_System/tasks/TASK-080.json`

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/scripts/limit_watcher.py` | YES |
| `MAP_System/scripts/start-limit-watcher.sh` | YES |
| `MAP_System/tests/test_limit_watcher.py` | YES |
| `MAP_System/notes/limit-exhaustion-protocol.md` | YES |
| `MAP_System/agents/limit-watcher-state.json` | YES |

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| The watcher can auto-open paid agent sessions. | MEDIUM | Accepted with mitigations: visible terminal tabs, no headless path, one-nudge-per-window state, and durable event logging. |
| PID checks are namespace-sensitive in this environment. | LOW | Launcher now identity-checks `/proc/<pid>/cmdline`; reviewer used state-file mtime deltas for namespace-proof liveness. |
| `CHANGES_REQUESTED` currently lacks a first-class rework transition. | LOW | Track as follow-up tooling work; Claude had to repair task state via minimal SQL before normal claim/resubmit. |

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| OPTIONAL | `MAP_System/db/claims.py` / `MAP_System/scripts/map_task.py` | task lifecycle | First real CHANGES_REQUESTED flow exposed that rejected tasks do not have a clean rework transition back to READY/claimed/resubmitted. | Add a first-class rework transition in a follow-up task. |

No BLOCKER or REQUIRED findings.

---

## Notes

Previous REQUIRED findings are resolved:

- Empty successful hcom list now returns `[]`, not `None`.
- Live watcher verification should not rely on reviewer-local `kill -0` across PID namespaces. State-file mtime advanced from `2026-07-02 00:33:44 -0400` to `2026-07-02 00:34:44 -0400`, matching the 60s poll interval.

Verification performed:

- `python3 MAP_System/tests/test_limit_watcher.py`: 8 tests passed.
- `MAP_System/scripts/run_tests.sh`: `pass=19 fail=0 total=19`.
- `python3 MAP_System/scripts/validate_task_graph.py`: passed.
- `python3 MAP_System/scripts/validate_events.py`: 0 errors, 33 historical warnings.
