<!-- hpom: file: artifacts/reviews/task187-review-toku.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: TASK-187 submitted diff + local verification run -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Review Record: TASK-187

## Header

```
task_id:      TASK-187
reviewer:     claude-lab-toku
review_date:  2026-07-14
task_owner:   codex-lab-nivo
```

Reviewer (claude-lab-toku) ≠ task owner (codex-lab-nivo). Independence check passes.

Combined-diff scope note: per the output-path handoff recorded in
`artifacts/tests/task-186-rns-suppression-evidence.md` (hcom #34173),
this review covers the full working-tree diff of `limit_watcher.py` and
`test_limit_watcher.py`, which includes TASK-186's terminal-suppression
helpers (`is_terminal_session`, `close_terminal_incidents`,
`detect_terminal_suppressions` + `poll_once` wiring) authored under
claude-lab-mira's ownership. The reviewer had no part in TASK-186 or
TASK-187 implementation; independence holds for both halves.

---

## Verdict

```
APPROVED
```

---

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `send_nudge` detects the hcom "still active" resume failure and falls back to sending the RnS prompt to the active session | PASS | `ACTIVE_SESSION_RESUME_RE` (`\bstill active\b`, case-insensitive) checked against non-zero-exit stdout+stderr in `is_active_session_resume_failure()`; fallback is `hcom send @<agent> --intent inform` carrying the full `NUDGE_PROMPT`. Independently verified the real hcom v0.7.23 binary emits a message containing `" is still active "` (`strings ~/.local/bin/hcom`), so the regex matches the real failure text, not just the test fixture. |
| 2 | Fallback preserves visible-terminal resume behavior for stopped sessions and does not use headless mode | PASS | Resume command unchanged: `hcom r <agent> --terminal wezterm-tab --go`; fallback path only fires after a still-active failure and uses `hcom send` (message, no session spawn). `--headless` appears nowhere in the diff; `test_send_nudge_resume_success_keeps_visible_terminal` pins both. |
| 3 | Tests cover normal resume success, active-session fallback success, and active-session fallback failure | PASS | `test_send_nudge_resume_success_keeps_visible_terminal` (2 calls, no fallback), `test_send_nudge_active_session_fallback_sends_prompt` (3 calls, prompt content asserted), `test_send_nudge_active_session_fallback_failure_returns_false` (send fails → False). A non-"still active" resume failure still returns False unchanged (regex guard). |
| 4 | Focused limit watcher tests, validate_events --fail-on-new, validate_task_mirrors, and full MAP tests pass | PASS | Reproduced locally by this reviewer: `test_limit_watcher.py` 25/25; `validate_events.py --fail-on-new` errors=0 new_warnings=0 (33 legacy baseline); `validate_task_mirrors.py` passed; `run_tests.sh` SUMMARY pass=56 fail=0. |

TASK-186 handed-off code (reviewed as part of the combined diff):

| # | Check | Result | Evidence |
|---|---|---|---|
| 5 | Suppression code not weakened by TASK-187 changes | PASS | TASK-187's diff touches only `send_nudge`/new fallback helpers + constants; the terminal-suppression block in `poll_once` and the three helpers are byte-identical to the owner-verified TASK-186 state (single combined diff inspected line-by-line). |
| 6 | Terminal classification is conservative | PASS | `is_terminal_session` requires durable `status == "inactive"` AND reason ∈ {`session_superseded`, `disposable_session_ended`}; `test_terminal_session_classification` pins the negative cases (`out_of_tokens`, `standby`, missing reason). |
| 7 | Closures/suppressions are visible, never silent | PASS | Every popped incident gets `closed_reason: "terminal_session"` + printed line + PROGRESS event (task_id TASK-186); suppressions print each transition poll and event once (guarded by `state["terminal_suppressed"]`). |
| 8 | Terminal sessions cannot re-enter incident/probe/nudge paths | PASS | `detect_presumed_down` skips any entry with a recorded `reason` (pre-existing, line ~157), so terminal agents can never re-open incidents; `test_terminal_entries_suppressed_in_checkins_work_nudges_and_v1_nudges` pins checkin/work-nudge/v1-resume paths, including a lingering passed `resume_after`. |

---

## Forbidden Changes Check

| Forbidden change | Status |
|---|---|
| Headless resume mode (protocol: "never headless") | NOT BROKEN — visible `--terminal wezterm-tab` path unchanged; fallback is a message, not a spawn |
| Weakening TASK-186 suppression semantics | NOT BROKEN — helpers and `poll_once` wiring unaltered by the TASK-187 changes |
| Silent failure handling (RnS visibility rule) | NOT BROKEN — non-"still active" failures still return False and are logged as FAILED by callers |

---

## Files Reviewed

- `MAP_System/scripts/limit_watcher.py` (combined TASK-186 + TASK-187 diff, +76)
- `MAP_System/tests/test_limit_watcher.py` (+170, 7 new tests: 4 TASK-186, 3 TASK-187)
- `MAP_System/notes/limit-exhaustion-protocol.md` (+3, documents the fallback)
- `MAP_System/artifacts/tests/task-186-rns-suppression-evidence.md` (handoff basis, read-only)

---

## Scope Check

| Changed file | In scope? |
|---|---|
| `MAP_System/scripts/limit_watcher.py` | YES — TASK-187 output path (carries handed-off TASK-186 hunks per the logged handoff) |
| `MAP_System/tests/test_limit_watcher.py` | YES — TASK-187 output path (same handoff) |
| `MAP_System/notes/limit-exhaustion-protocol.md` | YES — TASK-187 output path |

No other watcher-related files changed in the working tree.

---

## Risk Identification

| Risk | Severity | Recommended action |
|---|---|---|
| hcom error text drift: a future hcom version could reword "still active", silently disabling the fallback (resume would return False as before — degraded, not dangerous) | LOW | None now; if hcom is updated (v0.7.23 → newer is already advertised), re-run the strings check or add the message shape to an hcom-upgrade checklist |
| `state["terminal_suppressed"]` grows without pruning and is not cleared if a terminal agent is later marked `--back`; a re-terminal transition for the same name would print but not event | LOW | OPTIONAL follow-up: prune alongside `prune_absent_session_tracking` and drop entries whose durable record is no longer terminal |
| Fallback success reported as nudge success in incident bookkeeping (`probes_sent` increments, event says "nudge sent") — accurate enough, but the event text does not distinguish resume-vs-fallback delivery | LOW | Acceptable; the fallback's own `!NOTE` message makes delivery mode visible in hcom |

---

## Findings

| Severity | File | Section | Finding | Required action |
|---|---|---|---|---|
| OPTIONAL | `scripts/limit_watcher.py` (send_nudge) | dry-run path | `--dry-run` prints only the resume command; the potential fallback branch is invisible in dry-run output | None required — dry-run can't know the resume would fail; note only |
| OPTIONAL | `scripts/limit_watcher.py` (poll_once) | terminal_suppressed | No pruning of `terminal_suppressed` map (see Risk 2) | Optional follow-up task; not a defect in this change |

No BLOCKER or REQUIRED findings.

---

## Notes

- Verification was reproduced by the reviewer from scratch, not taken from the
  submission: 25/25 focused tests, mirrors gate, event gate (new_warnings=0),
  and full suite 56/56.
- The deciding check for criterion 1 was external: the fallback trigger regex
  was validated against the actual hcom binary's error string rather than only
  the fabricated test fixtures — the real message contains `" is still active "`,
  so the real-world failure from the 2026-07-14 Mira scheduled-RnS incident
  would now take the fallback path.
- TASK-186's live-marks "after evidence" section remains PENDING OPERATOR
  ACTION in its evidence artifact; that is TASK-186's remaining work under
  mira's ownership and does not gate this review of the frozen watcher code.
