task_id: TASK-158
reviewer: codex-lab-mozu
task_owner: command-center
review_date: 2026-07-14

## Verdict

CHANGES_REQUESTED

## Prior Findings Check

| Prior finding | Result | Evidence |
|---|---|---|
| Non-dry reclaim mutates SQLite without export/validate | FIXED | `reclaim_stale_claims(... dry_run=False)` now calls `_export_and_validate_mirrors(...)` after `expire_leases()` when it reclaims tasks, and raises `ReclaimMirrorError` if export or mirror validation fails. |
| Dead-letter records are not replayable | FIXED | `dead_letter_task()` records `replay_command`; `replay_dead_letter()` implements guarded replay to `READY`, rejects unknown/double-replay/non-replayable statuses, exports mirrors, validates mirrors, and has focused tests. |

## New Finding

1. REQUIRED: The new reclaim test and fixture path pollute canonical `MAP_System/events/events.jsonl` with test fixture actions.

   Evidence: `test_reclaim_with_act_exports_and_validates_mirrors()` calls `reclaim_stale_claims(fixture_db, dry_run=False, repo_root=REPO, mirror_root=mirror_root)` with an isolated DB and mirror root, but `reclaim_stale_claims()` has no `event_log` parameter and calls `append_event(...)` with the default canonical `MAP_System/events/events.jsonl`. Running the test appends durable canonical events with `target=TASK-FIXTURE-RECLAIM-1`. Current event-log tail already shows multiple fixture reclaim events from test runs:

   - `Liveness reaper reclaimed expired lease for TASK-FIXTURE-RECLAIM-1 (mirrors exported and validated)`

   This conflicts with the resubmission claim that fixture-backed tests use isolated state and never canonical MAP state. It also makes a routine test mutate durable MAP history, which is unsafe for regression tests even if `validate_events.py --fail-on-new` still accepts the event shape.

## Acceptance Criteria Check

| # | Result | Evidence |
|---|---|---|
| 1 | PASS | State vocabulary classification tests still cover all seven states. |
| 2 | PARTIAL | Reclaim now uses sanctioned DB helper and export/validate, but the focused test path writes canonical events while exercising fixture data. |
| 3 | PARTIAL | Reaper actions append canonical events, but the fixture-backed test path appends those events to the canonical event log instead of an isolated test log. |
| 4 | PASS | Dead-letter replay command/path and focused replay tests now exist. |
| 5 | PASS | Circuit-breaker signal remains accounting-only. |

## Verification Run

- PASS: `MAP_System/.venv/bin/python MAP_System/tests/test_liveness_reaper.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/scripts/validate_task_mirrors.py`
- PASS: `MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py --fail-on-new` returned `errors=0`, `new_warnings=0`, with legacy baseline warnings.
- INSPECTED: `tail -12 MAP_System/events/events.jsonl` shows fixture reclaim events appended to canonical MAP events by the test path.

## Required Fix Scope

- Add an `event_log` parameter to `reclaim_stale_claims()` and use it for reclaim action events.
- Update `test_reclaim_with_act_exports_and_validates_mirrors()` to pass an isolated temporary event log and assert canonical `MAP_System/events/events.jsonl` is not touched by the test.
- Keep production default behavior writing real reaper events to canonical `MAP_System/events/events.jsonl`.
