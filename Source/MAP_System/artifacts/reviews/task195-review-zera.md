<!-- hpom: file: artifacts/reviews/task195-review-zera.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: TASK-195 independent review -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Review Record: TASK-195

## Header

```
task_id:      TASK-195
reviewer:     claude-lab-zera
review_date:  2026-07-15
task_owner:   codex-lab-nivo
```

Reviewer (claude-lab-zera) != task owner (codex-lab-nivo). Independence check passes.

---

## Verdict

```
APPROVED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `send_nudge` returns false instead of raising when `hcom r` times out | PASS | `scripts/limit_watcher.py` `send_nudge` now wraps the `hcom r` subprocess call in `try/except subprocess.TimeoutExpired` (and `OSError`), logging a warning and returning `False` instead of propagating. Reproduced directly with `tests/test_limit_watcher.py::test_send_nudge_resume_timeout_returns_false`, which monkeypatches `subprocess.run` to raise `TimeoutExpired` on the `hcom r` call and asserts `send_nudge(...) is False` with no exception. Ran the test: PASS. |
| 2 | `poll_once` records failed nudge events and the watcher process keeps running after a hung resume | PASS | `poll_once` now tracks `state["failed_nudges"][agent] = {resume_after, last_failed_at}` on a failed send, backs off re-nudging via `RECORDED_RESET_FAILURE_RETRY_SECONDS` (300s) in `decide_nudges`, and always appends a `PROGRESS` event noting `visible resume nudge FAILED` rather than raising. Since `send_nudge` no longer raises (criterion 1), the surrounding `poll_once` loop cannot be killed by a hung resume. Also live-confirmed in the actual repo's `events/events.jsonl`: four real `RnS: recorded resume window passed ... visible resume nudge FAILED` entries exist from 2026-07-15, i.e. this code path already ran for real and the watcher kept polling afterward (no gap in subsequent PROGRESS/TASK-196 events). Backoff logic verified directly: `test_failed_recorded_reset_retry_throttle` confirms re-nudge is suppressed <5min after a failure and allowed again after. |
| 3 | Command center RnS health can distinguish stale/dead watcher pidfile from normal warning state | PASS | `/home/home/Projects/CommandCenterUI/app/server.py` adds `watcher_process_health()`: missing pidfile -> `warn` ("watcher pidfile missing"), unreadable pidfile -> `error`, pid not present in `/proc` -> `error` ("watcher pidfile stale (pid N not running)"), pid present but not `limit_watcher.py` -> `error`, matching live process -> `ok`. `rns_health()` folds this into overall status (process `error` always wins; process `warn` only escalates an otherwise-`ok` status). Manually imported `server.py` and exercised `watcher_process_health()` three ways: real pidfile -> `ok` (live pid), a monkeypatched stale pid (999999999) -> `error`/"pidfile stale", missing pidfile -> `warn`. All three matched the intended semantics exactly — this is a live-behavior check, not just a code read. |

---

## Files Reviewed

- `MAP_System/scripts/limit_watcher.py` (diff, full read of the changed sections)
- `MAP_System/tests/test_limit_watcher.py` (diff, full read of new tests)
- `/home/home/Projects/CommandCenterUI/app/server.py` (diff — note: this file also carries substantial unrelated uncommitted changes from other in-flight work, see Risks/Notes; isolated and reviewed only the `watcher_process_health`/`rns_health` hunk relevant to this task's output scope)

## Forbidden Changes Check

`limit_watcher.py`/`test_limit_watcher.py` changes are scoped to the nudge-failure/backoff/liveness-clearing paths described by the task; no unrelated logic touched. `server.py`'s `watcher_process_health`/`rns_health` hunk is scoped correctly, but that file's working tree also contains other, unrelated diffs (summary-model swap, new relay prompt, new local-agent launcher defs, ProjectUpdater embed) that are not part of this task's declared scope — flagged below, not attributed to this task's authorship since output_paths/acceptance criteria only concern the watcher-health function.

## Risks / Notes

- `CommandCenterUI/app/server.py` has no test suite; the pidfile-health verification here was done by direct interactive exercise (documented under Reproduction) rather than an automated regression test. Consider a lightweight `test_server_health.py` in a follow-up if this file keeps growing.
- `server.py`'s working tree currently mixes TASK-195's watcher-health hunk with unrelated changes (SUMMARY_MODEL/SUMMARY_PROMPT rewrite, `BASE_LOCAL_AGENT_DEFS`, ProjectUpdater command bridge) that read as separate feature work, not part of TASK-195. Not a defect in TASK-195 itself, but whoever owns those other changes should get them into their own task/commit rather than riding along in this file's diff — flagging so it doesn't get silently attributed to this review.
- MAP suite: 63/63 pass (`scripts/run_tests.sh`), `tests/test_limit_watcher.py`: 28/28 pass.

## Reproduction

```
cd MAP_System
.venv/bin/python tests/test_limit_watcher.py     # 28 limit_watcher tests passed
bash scripts/run_tests.sh                        # SUMMARY pass=63 fail=0 total=63

cd /home/home/Projects/CommandCenterUI
python3 -c "
import importlib.util
spec = importlib.util.spec_from_file_location('server', 'app/server.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(m.watcher_process_health())   # live: {'status': 'ok', ...}
"
```
