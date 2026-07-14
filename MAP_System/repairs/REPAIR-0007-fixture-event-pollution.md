# Repair Record

Repair ID: REPAIR-0007
Related task: TASK-158
Found by: codex-lab-mozu (rereview finding), fixed by claude-lab-zera
Date: 2026-07-14
Severity: DRIFT
Status: APPLIED

## What was found

`MAP_System/events/events.jsonl` contains 6 lines (~2026-07-14T01:05-01:11Z)
reporting "Liveness reaper reclaimed expired lease for TASK-FIXTURE-RECLAIM-1"
— a task ID that never existed as a real MAP task. These were written by
`test_liveness_reaper.py`'s `test_reclaim_with_act_exports_and_validates_mirrors`
test, which used a fixture task ID against an isolated copy of `map.db` but
called `reclaim_stale_claims()` without an `event_log` override — that
function had no such parameter, so every real-reclaim call (including from
the test) appended to canonical `MAP_System/events/events.jsonl` regardless
of which `db_path` was passed.

## Surfaced by

codex-lab-mozu's TASK-158 rereview (`artifacts/reviews/task158-rereview-mozu.md`),
found while re-verifying the first round of review fixes.

## Severity rationale

DRIFT: the event log now contains factually incorrect entries (a
task/action that never really happened), but nothing is blocked — no
task/mirror state was corrupted, no gate failed, and `validate_events.py`
still parses these lines as well-formed canonical events. This is a
data-quality drift, not a structural or authority issue.

## Proposed or applied fix

1. Code fix: added an `event_log: Path = DEFAULT_EVENT_LOG` parameter to
   `reclaim_stale_claims()` in `scripts/liveness_reaper.py`, threaded
   through to its `append_event()` call. (`dead_letter_task()` and
   `replay_dead_letter()` already had this parameter — only the reclaim
   path was missing it.)
2. Test fix: `test_reclaim_with_act_exports_and_validates_mirrors` now
   passes an isolated temp `event_log` path, matching the pattern already
   used by the dead-letter/replay tests.
3. Log fix: per `events/README.md` ("Do not rewrite old events unless the
   operator explicitly asks for log repair"), the 6 polluted lines were
   NOT deleted or edited in place. Instead, one corrective `PROGRESS` event
   was appended marking them void and pointing to this repair record —
   consistent with the repo's append-forward convention (see
   `notes/brain-compaction-guide.md`'s "summarize forward" pattern).

## Authority check

- [x] DRIFT or mechanical BLOCKING — core agent applied directly

## Verification

- `python3 MAP_System/tests/test_liveness_reaper.py` — all 12 tests pass,
  including the fixed reclaim test.
- `grep -c "TASK-FIXTURE" MAP_System/events/events.jsonl` — unchanged after
  the fix (no new pollution added by a re-run of the test suite).
- `python3 MAP_System/scripts/validate_events.py --fail-on-new` —
  errors=0, new_warnings=0 (the corrective event and the original polluted
  lines are all schema-valid; this repair addresses factual accuracy, not
  schema shape).
- `python3 MAP_System/scripts/run_tests.sh` — full suite green (43/43 at
  time of this repair).

## Recurrence check

- [x] First occurrence of this drift class

## Notes

This is the second review round on TASK-158 (first round: reclaim mirror
export/dead-letter replay, both fixed and covered by fixture tests; this
round: the fixture tests themselves needed event-log isolation, which is
exactly the kind of thing a fixture-backed test for a write-path function
must double-check before it's trusted). General lesson worth carrying
forward: any test that calls a function performing real writes (DB, files,
event log) must verify **every** side-effecting parameter has an
override, not just the ones the test happens to already isolate.
