# Cost/Yield Rollup — 2026-07-14

Task: TASK-190
Author: claude-lab-zero (owner)
Source pattern: `repo/codeburn-main/src/yield.ts` (productive/reverted/abandoned
yield buckets), adapted to MAP's status taxonomy per the work packet
`MAP_System/inbox/helpers/cost-yield-rollup-packet.md`.
Tool: `MAP_System/scripts/cost_yield.py` (text + `--json`; read-only,
`mode=ro` DB connection, no event writes)
Tests: `MAP_System/tests/test_cost_yield.py` (5 tests, wired into
`run_tests.sh` as `cost_yield_test`)

## Proxy disclaimer

All cost signals below are PROXIES: per-task event volume from
`events/events.jsonl`, wall-clock activity span (first event → last event),
attempts, and rework rounds (CHANGES_REQUESTED events). MAP records no
per-task token or currency data, so no dollar figures are computed or
implied anywhere in this rollup.

## Outcome classes

- released — status RELEASED (productive)
- approved_not_released — status APPROVED, awaiting release gate
- retired — status RETIRED (deliberately discarded: duplicates/cancelled)
- abandoned — any other terminal-but-unreleased status (FAILED/CANCELLED;
  currently zero tasks)
- legacy_done — status DONE. Kept OUT of abandoned deliberately: all 25 DONE
  rows are pre-release-gate bootstrap completions (every one carries the
  2026-07-02T12:35:20Z migration-import timestamp, and the first
  `task_release_records` row is 2026-07-02T12:39:21Z — the gate did not exist
  when they finished). Counting them as abandoned spend would misstate the
  split. Approved by claude-lab-mira over hcom (#34199) before implementation.
- in_flight — non-terminal statuses (READY/IN_PROGRESS/SUBMITTED/…)

## Real rollup output (repo state as of 2026-07-14)

Command: `python3 MAP_System/scripts/cost_yield.py`

```
MAP Cost/Yield Rollup

Note: Cost signals are PROXIES (event volume, wall-clock activity span, attempts, rework rounds) -- not dollars. No currency data exists per task and none is fabricated here.

Tasks: 180  |  events attributed: 991  |  unattributed: 46  |  unknown-task: 38

Outcome classes (proxy spend)
| Outcome | Tasks | Events | Event % | Span h | Attempts | Rework |
|---|---:|---:|---:|---:|---:|---:|
| released | 94 | 539 | 54.4% | 2990.28 | 108 | 24 |
| approved_not_released | 52 | 370 | 37.3% | 404.83 | 62 | 14 |
| retired | 4 | 9 | 0.9% | 0.78 | 0 | 0 |
| abandoned | 0 | 0 | 0.0% | 0 | 0 | 0 |
| legacy_done | 25 | 67 | 6.8% | 390.43 | 25 | 2 |
| in_flight | 5 | 6 | 0.6% | 3.62 | 4 | 0 |

Productive vs abandoned split (by attributed events)
| Bucket | Tasks | Events | Event % | Span h |
|---|---:|---:|---:|---:|
| productive | 94 | 539 | 54.4% | 2990.28 |
| abandoned | 4 | 9 | 0.9% | 0.78 |
| pending | 57 | 376 | 37.9% | 408.45 |
| legacy | 25 | 67 | 6.8% | 390.43 |

Productive-to-abandoned event ratio: 59.89

Cost per released output (proxies)
| Metric | Value |
|---|---:|
| released_tasks | 94 |
| events_per_released_task_avg | 5.73 |
| span_hours_per_released_task_avg | 31.81 |
| attempts_per_released_task_avg | 1.15 |
| rework_rounds_per_released_task_avg | 0.26 |
| all_in_events_per_release | 10.54 |

Top 10 tasks by event volume
| Task | Outcome | Events | Span h | Attempts | Rework |
|---|---|---:|---:|---:|---:|
| TASK-083 | approved_not_released | 126 | 294.07 | 1 | 1 |
| TASK-181 | released | 59 | 0.77 | 1 | 0 |
| TASK-174 | approved_not_released | 38 | 1.47 | 2 | 1 |
| TASK-158 | approved_not_released | 17 | 0.55 | 3 | 2 |
| TASK-141 | released | 14 | 0.49 | 3 | 2 |
| TASK-144 | released | 14 | 0.28 | 1 | 0 |
| TASK-142 | released | 11 | 0.2 | 2 | 1 |
| TASK-145 | released | 11 | 0.18 | 1 | 0 |
| TASK-055 | legacy_done | 10 | 0.36 | 1 | 0 |
| TASK-103 | released | 10 | 0.16 | 2 | 2 |
```

## Reading of the numbers (operator summary)

- 54.4% of attributed event volume landed in RELEASED work; only 0.9% went
  to deliberately discarded (retired) work. The productive-to-abandoned event
  ratio is ~60:1 — very little proxy spend is being thrown away.
- The big open question the rollup surfaces is the PENDING bucket: 52
  APPROVED-not-released tasks carry 37.3% of all attributed spend. That work
  is done and reviewed but not yet through the release gate; releasing (or
  batch-releasing) it is the cheapest way to convert already-spent effort
  into yield.
- Cost of one released output at current yield: ~5.7 events within the task
  itself, ~10.5 events all-in (including overhead of pending/retired/legacy
  spend), ~1.15 attempts and ~0.26 rework rounds per release.

## Caveats

- TASK-083 (126 events, 294h span) is the RnS limit watcher's attribution
  task: the watcher stamps its ongoing operational events on TASK-083, so its
  "cost" reflects runtime monitoring activity, not implementation effort.
  Span-hours in general measure first-to-last event distance, not effort —
  long-lived operational tasks dominate that column (hence released span of
  2990h; TASK-181's emergence-compaction burst shows the opposite shape:
  59 events in 46 minutes).
- 46 events carry no task_id (bootstrap decisions, workspace notes) and 38
  belong to task_ids absent from map.db (AD-HOC-* and COMMAND-CENTER-UI-*
  work done outside the task pipeline). Both are counted and surfaced in the
  totals rather than silently dropped, but excluded from per-class percents.
- Event volume under-counts tasks whose discussion happened over hcom rather
  than events.jsonl; it is a floor, not a measure of total effort.

## JSON summary (same run, `--json`, abridged to the summary blocks)

```json
{
  "cost_by_released_output": {
    "all_in_events_per_release": 10.54,
    "attempts_per_released_task_avg": 1.15,
    "events_per_released_task_avg": 5.73,
    "released_tasks": 94,
    "rework_rounds_per_released_task_avg": 0.26,
    "span_hours_per_released_task_avg": 31.81
  },
  "spend_split": {
    "abandoned": {"event_percent": 0.9, "events": 9, "span_hours": 0.78, "tasks": 4},
    "legacy": {"event_percent": 6.8, "events": 67, "span_hours": 390.43, "tasks": 25},
    "pending": {"event_percent": 37.9, "events": 376, "span_hours": 408.45, "tasks": 57},
    "productive": {"event_percent": 54.4, "events": 539, "span_hours": 2990.28, "tasks": 94},
    "productive_to_abandoned_event_ratio": 59.89
  },
  "totals": {
    "events_attributed": 991,
    "events_unattributed": 46,
    "events_unknown_task": 38,
    "tasks": 180
  }
}
```
