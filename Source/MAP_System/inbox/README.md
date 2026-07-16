# Inbox

Inbox files are scoped agent-to-agent notes.

Use this directory when a message is more durable than chat but not broad enough
to belong in `shared/`.

## Subdirectories

- `codex/` - notes intended for Codex.
- `claude/` - notes intended for Claude Code.
- `helpers/` - notes for temporary helper agents.

Prefer handoffs when a note transfers responsibility for active work. Prefer
events for short status records.

## Communication Rules

Direct notes between helpers and non-owning core agents are allowed for bounded
questions. Record enough context that the owning core agent can understand what
was asked and answered.

Do not use inbox notes to silently change task ownership, priority, scope, or
approval state. Use a handoff, task update, event, or decision record instead.

See `../notes/communication-guide.md`.

## Threaded Messages

Use a thread ID when a note may need replies or later lookup:

```text
THREAD-TASK-048-review-scope
```

Use `../templates/inbox-message.md` for single-message notes and
`../templates/communication-thread.md` for longer exchanges.

If the exchange produces a durable decision, task change, handoff, or review,
summarize the result in the canonical location and leave a backlink in the inbox
note.
