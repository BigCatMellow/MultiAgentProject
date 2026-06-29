# Templates

Reusable templates for MAP-style project memory and coordination.

Copy these when creating new tasks, handoffs, reviews, decisions, or status
updates. Replace bracketed placeholders before committing the new file or entry.

## Files

- `task.json` - task record template.
- `handoff.md` - agent-to-agent handoff template.
- `inbox-message.md` - single durable message template.
- `communication-thread.md` - multi-message thread template.
- `review.md` - independent review template.
- `decision.md` - decision entry template.
- `current-state.md` - current-state document template.
- `compaction-summary.md` - archive summary template for brain compaction.
- `event.jsonl` - one-line event example.

Templates are examples, not canonical state. Canonical project truth belongs in
`shared/`, task records, workflow files, and append-only events.

All templates should follow `../notes/documentation-style-guide.md`: structured
fields, IDs, statuses, paths, and bullets before prose.
