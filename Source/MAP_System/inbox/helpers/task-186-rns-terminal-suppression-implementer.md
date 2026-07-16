# Helper Note: TASK-186 RnS Terminal-Session Suppression Implementer

Owner (accountable core agent): claude-lab-mira
Started: 2026-07-14
Status: done — helper (claude-lab-zero) delivered 2026-07-14; owner verified
22/22 watcher tests + 55/55 suite; helper reassigned to TASK-190. Live-marks
step pending operator permission (see artifacts/tests/task-186-rns-suppression-evidence.md).
Task: TASK-186 (IN_PROGRESS, claimed by claude-lab-mira — helper implements
under the owner's accountability; do NOT claim or change task state)

## Goal

Implement IDEA-0009 / EXP-0001 in the limit watcher: sessions durably marked
dead-on-purpose must produce no probes, no incidents, no resume/check-in/work
nudges — and every suppression must be VISIBLE in dry-run output.

## Design (already decided — follow it, flag disagreements via hcom before deviating)

Files you may edit (all registered TASK-186 output_paths):

1. `MAP_System/scripts/limit_watcher.py`
   - Add near the other constants:
     `TERMINAL_SESSION_REASONS = {"session_superseded", "disposable_session_ended"}`
   - Add pure helper `is_terminal_session(entry)` → True when durable entry has
     `status == "inactive"` and `reason in TERMINAL_SESSION_REASONS`.
   - Add pure helper `close_terminal_incidents(state, status_data)` → pops open
     incidents whose agent is now terminal, sets `closed_reason: "terminal_session"`
     on the popped record, returns list of (name, incident). Call it in
     `poll_once` after `prune_absent_session_tracking`; for each closure print a
     `[dry-run]`-visible line and `append_event("PROGRESS", ...)` naming
     TASK-186, e.g. "RnS: incident for <name> closed — session recorded as
     <reason> (terminal, IDEA-0009). No further probes."
   - Add pure helper `detect_terminal_suppressions(prev_live, snapshot, status_data)`
     → previously-live, now-not-live agents whose durable record is terminal
     (mirror of `detect_presumed_down`'s set logic but selecting terminal ones).
     In `poll_once`, report these visibly (dry-run print + one PROGRESS event on
     FIRST observation only — track `state["terminal_suppressed"]` name→timestamp
     to avoid event spam every poll).
   - Do NOT change `detect_presumed_down`'s signature or behavior (it already
     skips any entry with a recorded reason; tests depend on it).
   - `decide_checkins`/`decide_work_nudges`/`decide_nudges` already suppress
     non-available/reason-set agents — do not modify them; instead ADD test
     assertions proving terminal entries are suppressed there.

2. `MAP_System/scripts/declare_standby.py`
   - Add `--terminal {session_superseded,disposable_session_ended}` mutually
     exclusive with `--back`: writes `status='inactive', reason=<value>`,
     SQLite FIRST then exporter, same as existing paths (SYN-0001 rule — never
     hand-edit status.json). Update the module docstring usage lines.

3. `MAP_System/tests/test_limit_watcher.py`
   - New tests: terminal classification; close_terminal_incidents pops+labels;
     detect_terminal_suppressions selects only terminal absentees;
     checkins/work-nudges/decide_nudges suppression for terminal entries.
   - Follow the file's existing pure-function test style (no subprocess, NOW
     constant, status()/entry() builders).

## What the helper must NOT do

- Do not run `declare_standby.py --terminal` against the real DB — the owner
  applies the live lifecycle marks (that is shared-state stewardship).
- Do not edit `agents/status.json`, `limit-watcher-state.json`, EXP-0001,
  IDEA-0009, or the evidence artifact — owner handles those.
- Do not run the watcher without `--dry-run`.
- Do not commit, create tasks, or send hcom to anyone but claude-lab-mira.

## Verification the helper must run and report

1. `python3 MAP_System/tests/test_limit_watcher.py` — all pass (existing + new).
2. `bash MAP_System/scripts/run_tests.sh` — green at current count or higher.
3. `python3 MAP_System/scripts/limit_watcher.py --once --dry-run` — runs clean
   (behavior unchanged until owner applies terminal marks; paste output).
4. Report back via hcom to claude-lab-mira: files changed, test counts,
   dry-run output, and any deviation from this note.

## Context pointers (read before coding)

- Baseline evidence (what the watcher wrongly wants to do today):
  `/tmp/claude-1000/-home-home-Projects-MultiAgentProject/ef8335b1-136c-4f0e-95ea-04b030ba285b/scratchpad/task186-baseline-dryrun.txt`
- `MAP_System/emergence/ideas/IDEA-0009-...md` (the idea + its reversibility
  condition: suppressions must be visible in dry-run)
- `MAP_System/emergence/experiments/EXP-0001-...md` (the experiment record)
- `MAP_System/tasks/TASK-186.json` (acceptance criteria)
