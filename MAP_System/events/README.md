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

## Validation

Run:

```bash
python3 MAP_System/scripts/validate_events.py --fail-on-new
```

`events/warning_baseline.json` records the accepted historical warning line
count. Warnings at or before that line are legacy noise; warnings after it are
new signal and should be fixed before release.
