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
CHANGES_REQUESTED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Watcher nudges an agent at most once per resume_after window (no spawn loops) | PASS | `decide_nudges()` skips when `state["nudged"][agent] == resume_after`; `test_one_nudge_per_window` covers old and new windows. |
| 2 | All resumes use --terminal wezterm-tab, never headless, per operator visibility rule | PASS | `send_nudge()` builds `hcom r <agent> --terminal wezterm-tab --go --hcom-prompt ...`; no `--headless` path found. |
| 3 | Unparseable resume_after values are skipped with a durable warning, not guessed | PASS | Live event line 287 flags antigravity's free-text value; `warned_unparseable` suppresses repeats. |
| 4 | Silent stops (agent gone from hcom without status.json update) produce a durable event | FAIL | `hcom_live_agents()` returns `None` on an empty successful hcom list, so `poll_once()` skips silent-stop detection when all previously live agents vanish. |
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
| Watcher can auto-open paid agent sessions. | MEDIUM | Keep visible-tab requirement and one-nudge-per-window guard; add/keep tests around command construction before approval. |
| A stale pidfile can make the operator believe recovery automation is live when it is not. | MEDIUM | Resubmit only after the watcher is verified alive in the intended runtime environment, not just pidfile-present. |

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| REQUIRED | `MAP_System/scripts/limit_watcher.py:143` | `hcom_live_agents()` | A successful `hcom list --names` with no live agents produces an empty list, but the function returns `None` because of `return names or None`. `poll_once()` treats `None` as "hcom unavailable" and skips silent-stop detection. This breaks the most important recovery case: all previously live agents vanish while `agents/status.json` still says available. | Return `names` for successful hcom calls, even when empty, and add a regression test covering empty live-list behavior through the polling path or a helper that represents `hcom_live_agents()`. |
| REQUIRED | `MAP_System/.locks/limit-watcher.pid` | live process | The submitted task says the watcher is running live, but the pidfile pointed to dead PID `275543`. Restarting with `start-limit-watcher.sh` created a new PID that also exited within seconds in this environment, leaving only a stale pidfile and no log output. | Resubmit with the watcher actually running in a durable runtime visible to the operator, or update the launcher/protocol to use a runtime that survives agent command completion. Include verification stronger than pidfile presence: `kill -0 $(cat MAP_System/.locks/limit-watcher.pid)` and `ps -fp ...` after a short wait. |

No BLOCKER findings. REQUIRED findings must be fixed before approval.

---

## Notes

Verification performed:

- `python3 MAP_System/tests/test_limit_watcher.py`: 7 tests passed.
- `MAP_System/scripts/run_tests.sh`: `pass=19 fail=0 total=19`.
- `python3 MAP_System/scripts/validate_task_graph.py`: passed.
- `python3 MAP_System/scripts/validate_events.py`: 0 errors, 33 historical warnings.
- `python3 MAP_System/scripts/limit_watcher.py --once --dry-run`: exited 0.

The antigravity `resume_after` free-text value is correctly reported as unparseable; I did not change `agents/status.json` because no actual reset timestamp is available to write.
