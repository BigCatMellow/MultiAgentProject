# Events

`events.jsonl` is the append-only activity log for short durable updates.

Use events for compact records such as:

- progress;
- submissions;
- review requests;
- approvals;
- changes requested;
- questions and answers;
- handoff notices;
- decisions proposed or recorded.

Use handoffs or artifacts for longer context. Do not rewrite old events unless
the operator explicitly asks for log repair.

## Outcome Feedback

Use `outcome_pass` and `outcome_fail` for later-use feedback after a task has
shipped. These events are distinct from validation and review events: they
record whether real use later showed the released work behaved as intended.

Outcome records must include these fields, either as top-level JSONL fields or
as a JSON object in `summary` for compatibility with the current SQLite
`events` table:

- `outcome_id`
- `observed_at`
- `observed_by`
- `outcome_status`: `pass`, `fail`, `partial`, `unknown`, or `not_exercised`
- `validation_status_at_ship`: `passed`, `failed`, `waived`, or
  `not_applicable`
- `review_status_at_ship`: `approved`, `changes_requested`, `waived`, or
  `not_applicable`
- `follow_up`: `none`, `repair`, `risk`, `validator_improvement`,
  `research`, or `task_backlog`

For failed outcomes, also include `failure_class` and `severity` when known.
`map_metrics.py` derives the validator blind-spot rate from these events:
known later outcomes for validation-passed work form the denominator, and
`outcome_fail` events in that denominator form the numerator.

## Validation

Run:

```bash
python3 MAP_System/scripts/validate_events.py --fail-on-new
```

`events/warning_baseline.json` records the accepted historical warning line
count. Warnings at or before that line are legacy noise; warnings after it are
new signal and should be fixed before release.
