# Handoffs

Handoffs preserve continuity when work moves between agents or sessions.

Use a handoff when another agent needs to review, continue, or resume work
without reconstructing context from chat.

## Naming

Use descriptive lowercase kebab-case names when creating new handoffs:

```text
handoff-task-048-codex-to-claude.md
state-snapshot-codex-20260627T143000.yaml
```

Older handoff names may use legacy uppercase formats. Do not rename historical
handoffs unless references are updated.

## Include

- task ID or scope;
- sender and intended recipient;
- current status;
- files changed or created;
- what needs review or continuation;
- known limitations or risks;
- verification already run.

## When Not To Use A Handoff

Use `events/events.jsonl` for short progress notes. Use `shared/decisions.md`
for durable approved decisions.
