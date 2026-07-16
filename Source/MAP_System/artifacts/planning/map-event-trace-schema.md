# MAP Event Trace Schema (TASK-149, Wave 2)

Status: draft-active
Owner: command-center
Built by: TASK-149
Implements: `scripts/validate_events.py` (`TRACE_FIELDS`), `tests/test_validate_events.py`

## Purpose

Closes the 6.13 Requirements gap: "track task-level traces across HPOM, hcom,
emergence, and task files" and the Simulation-TestDrive probe "can you see
one causal chain end-to-end?" (currently "Likely gap"). This document defines
the fields; `scripts/validate_events.py` recognizes and validates them.

## Fields

| Field | Meaning | Required? |
|---|---|---|
| `trace_id` | Groups all events belonging to one causal chain (one operator request → dispatch → subtasks → review → release). | Not yet required — recognized, validated when present. |
| `parent_event_id` | The event this one causally follows (e.g. a SUBMISSION's parent is the PROGRESS event that started the work). | Not yet required. Must not appear without `trace_id` on the same event (a parent link without a trace grouping is not reconstructable). |
| `actor` | The agent or human that performed the action (may differ from `sender`, which is who wrote the log line — usually the same, but not always, e.g. a helper acting on a core agent's behalf). | Not yet required. |
| `action` | Short verb phrase for what happened (`claim`, `submit`, `approve`, `halt`, `reject`). Distinct from `type`, which is the event-record category. | Not yet required. |
| `target` | What the action was performed on (a task ID, a file path, another agent ID). Often equals `task_id` but not always (e.g. an agent-status change targets an agent, not a task). | Not yet required. |
| `thread` | The hcom thread name, if the event corresponds to a threaded conversation. | Not yet required. |

`task_id` is already a REQUIRED field in the existing schema and is reused
as-is; it is not part of `TRACE_FIELDS`.

## Why Not Required Yet

Making these fields required immediately would fail `--fail-on-new` on every
future event appended by hand (the current, universal method — no append
helper exists yet per the master plan's Wave 2 item 2). That would turn a
visibility improvement into a release-blocking regression across the whole
project on day one. Instead:

- Absence causes no warning at all (zero behavior change for existing
  event-writing conventions).
- Presence is validated for shape: each field, if present, must be a
  non-empty string; `parent_event_id` without `trace_id` is flagged.
- This lets the schema exist, be validated, and be adopted incrementally —
  the event append helper (a follow-on task) can start emitting these fields
  by default, and once adoption is high enough, a later task can promote
  `trace_id` (at minimum) into `OPTIONAL_CANONICAL` (warn-if-missing) the
  same way `artifact_paths` already works, and eventually into `REQUIRED`.

## Promotion Path (for a future task, not built here)

1. Event append helper (Wave 2 item 2) defaults `trace_id` to the owning
   task's ID plus a short suffix when no explicit trace is given, and
   `actor`/`action`/`target` from its call signature.
2. Once most new events include `trace_id`, promote it to
   `OPTIONAL_CANONICAL` so omission is flagged (warn, not error).
3. A trace-reconstruction command (Wave 2 item 3, not built here) walks
   `events.jsonl` for all lines sharing a `trace_id`, ordered by
   `parent_event_id` links, and prints the causal chain — this is the
   direct fix for the Simulation-TestDrive's "Likely gap" on structured
   tracing.

## Backward Compatibility Verification

Ran `scripts/validate_events.py --fail-on-new` against the live
`events/events.jsonl` (821+ lines as of this task) before and after adding
`TRACE_FIELDS` recognition: `errors=0 legacy_warnings=33 new_warnings=0` in
both cases — no existing line references trace fields, so none is affected.

## Related Files

- `scripts/validate_events.py`
- `tests/test_validate_events.py`
- `events/README.md` [[events/README]]
- `MAP_System/artifacts/planning/map-613-master-implementation-plan.md` [[map-613-master-implementation-plan]] (Wave 2)
- `Guidelines/6.13/MAP-System/03-MAP-System-Requirements-Outline.md`
