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
