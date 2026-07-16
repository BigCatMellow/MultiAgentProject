<!-- hpom: file: artifacts/reviews/task195-review-toku.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: TASK-195 submitted diff + local verification -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Review Record: TASK-195

## Header

```
task_id:      TASK-195
reviewer:     claude-lab-toku
review_date:  2026-07-15
task_owner:   codex-lab-nivo
```

Reviewer (claude-lab-toku) ≠ task owner (codex-lab-nivo). Independence check
passes. Note: reviewer previously reviewed TASK-187, an earlier watcher
change to the same file; this review reads the full current diff on its own
merits rather than assuming prior familiarity.

---

## Verdict

```
APPROVED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `send_nudge` returns false instead of raising when `hcom r` times out | PASS | `send_nudge` wraps both `subprocess.run` calls in `try/except`: `subprocess.TimeoutExpired`/`OSError` on the announce call is logged and swallowed (non-fatal); the resume call's `TimeoutExpired` logs a warning and returns `False` explicitly. `test_send_nudge_resume_timeout_returns_false` reproduces a real `TimeoutExpired` raise from a mocked `subprocess.run` and confirms `send_nudge` returns `False` without propagating. |
| 2 | `poll_once` records failed nudge events and the watcher process keeps running after a hung resume | PASS | Both nudge paths (`decide_nudges` recorded-reset loop and the new `live_due_recorded_resets` loop) now branch on `ok`: success clears `failed_nudges` and updates `nudged`; failure records `failed_nudges[agent] = {resume_after, last_failed_at}` and the existing `PROGRESS`/FAILED event text is preserved. Because `send_nudge` no longer raises on a hung resume (criterion 1), `poll_once` cannot crash from this failure mode, and `main()`'s `while True: poll_once(...)` loop continues to the next iteration/sleep — verified by reading the loop (no try/except needed around it for this specific failure mode, since the exception is now caught at its source). |
| 3 | Command-center RnS health can distinguish stale/dead watcher pidfile from normal warning state | PASS | `CommandCenterUI/app/server.py` adds `watcher_process_health()`: missing pidfile → `warn`; unreadable pidfile → `error`; pid not running → `error` ("stale"); pid running but not `limit_watcher.py` → `error`; else `ok`. `rns_health()` now merges this process signal with the existing state-file check instead of overloading a single `warn` for both "no state file yet" and "watcher actually dead." |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Visible-terminal / no-headless resume mandate | NOT BROKEN — `hcom r <agent> --terminal wezterm-tab --go` unchanged; `test_send_nudge_resume_timeout_returns_false` re-pins `--headless` absence |
| TASK-186 terminal-suppression logic | NOT BROKEN — `is_terminal_session`/`close_terminal_incidents`/`detect_terminal_suppressions` and their `poll_once` wiring are untouched by this diff |
| TASK-187 active-session fallback | NOT BROKEN, refactored cleanly — the fallback body was extracted into `send_active_session_nudge()` and is now reused by the new `live_due_recorded_resets` path (`kind="recorded-reset-live"`) as well as the original still-active case; behavior (announce optional, `hcom send --intent inform` with `NUDGE_PROMPT`) is preserved, only the trigger sites multiplied |

---

## Files Reviewed

- `MAP_System/scripts/limit_watcher.py` (+119/-11)
- `MAP_System/tests/test_limit_watcher.py` (+80, 3 new tests)
- `/home/home/Projects/CommandCenterUI/app/server.py` (`watcher_process_health`, `rns_health` merge — reviewed the RnS-relevant hunk directly, see Risk note below on the surrounding diff)

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/scripts/limit_watcher.py` | YES — declared output path |
| `MAP_System/tests/test_limit_watcher.py` | YES — declared output path |
| `CommandCenterUI/app/server.py` | YES — declared output path; RnS-specific hunks (`watcher_process_health`, `rns_health` merge) match acceptance criterion 3 exactly |

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| The live `CommandCenterUI` working tree also carries substantial diffs unrelated to TASK-195's declared scope — `sync_rns_provider_limits`/`RNS_SYNC_NOTE_MARKER` provider-limit-sync code, and full rewrites of `chat.css`/`chat.html`/`chat.js`/`README.md` — none of which are named in TASK-195's `output_paths` or acceptance criteria | LOW (informational) | Not a defect in TASK-195's own changes; flagging so the eventual release/commit boundary for `CommandCenterUI` is drawn deliberately rather than bundling unrelated in-flight work under this task's release record. Recommend the release checklist name exactly which `server.py` hunks belong to TASK-195, or that the CommandCenterUI commit happen under whichever task actually owns the provider-limit-sync/chat-UI work. |
| `write_status()` overwrites `agents/status.json` directly from the watcher for the live-due-reset clear path, outside the usual `declare_standby.py`/`map_status.py` write surface | LOW | Read-modify-write is narrowly scoped (only clears `status`/`reason`/`resume_after` and strips one notes marker on a single agent entry) and only fires when `hcom` confirms the session is actually live; acceptable given the bug being fixed (a stale recorded reset blocking further resume attempts on an agent that's already back). No action required. |

---

## Findings

No BLOCKER or REQUIRED findings.

---

## Notes

- Verification reproduced independently: `test_limit_watcher.py` 28/28
  (25 pre-existing + 3 new), full `run_tests.sh` 63/63.
- The refactor of the active-session fallback into `send_active_session_nudge()`
  is a clean simplification — it removes the duplicated fallback-construction
  code TASK-187 introduced and reuses it correctly for the new
  live-due-recorded-reset case, rather than copy-pasting a third fallback
  block.
- `snapshot = hcom_snapshot()` was hoisted earlier in `poll_once` (previously
  computed later, before the v2 incidents section) so the new
  `live_due_recorded_resets` check can use it; confirmed the later `if
  snapshot is not None:` guard for `prune_absent_session_tracking` still
  reads correctly from the same variable — no behavior change to that path.
