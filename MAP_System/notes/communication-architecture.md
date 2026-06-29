# Communication Architecture

MAP communication should form traceable threads, not loose notes.

The goal is that a future agent can answer:

- Who asked?
- Who answered?
- What task or scope was involved?
- What files were relevant?
- Was the owning core agent copied?
- What decision or action came out of it?
- Where did the final outcome get recorded?

## Communication Layers

```text
events/events.jsonl
  Short activity breadcrumbs.

inbox/<agent>/ and inbox/helpers/
  Scoped questions, answers, and helper notes.

handoffs/
  Transfer of responsibility or continuation context.

artifacts/reviews/
  Formal review findings and verdicts.

shared/unresolved-questions.md
  Project-level open questions.

shared/decisions.md
  Approved durable decisions.
```

## Thread IDs

Use a stable thread ID when a communication has more than one message or may
need later lookup.

Recommended format:

```text
THREAD-TASK-NNN-short-topic
THREAD-YYYYMMDD-short-topic
```

Examples:

```text
THREAD-TASK-048-review-scope
THREAD-20260627-helper-routing
```

Include the thread ID in:

- inbox notes;
- helper notes;
- handoffs;
- review artifacts;
- event summaries when relevant.

## Message IDs

Use message IDs inside longer notes when multiple questions or replies happen in
one file.

Recommended format:

```text
MSG-001
MSG-002
```

Each reply should name the message it answers:

```text
Reply to: MSG-001
```

## Required Cross-References

Every durable communication should include as many of these as apply:

- `Thread`
- `Message`
- `Task`
- `Sender`
- `Recipient`
- `Owner`
- `Copied`
- `Input paths`
- `Output paths`
- `Related artifacts`
- `Requested action`
- `Due or urgency`
- `Outcome location`

`Outcome location` is where the final result lives, such as:

- `shared/decisions.md`
- `shared/unresolved-questions.md`
- `tasks/TASK-NNN.json`
- `artifacts/reviews/...`
- `handoffs/...`
- `events/events.jsonl`

## Promotion Rules

Not every message stays in the inbox.

Promote the result when:

- a question becomes a project-level open question;
- a recommendation becomes an approved decision;
- a note transfers responsibility;
- a finding becomes a formal review;
- a helper result changes task scope or output paths.

Promotion targets:

| If the result is... | Move or summarize it in... |
|---|---|
| Durable decision | `shared/decisions.md` |
| Open project question | `shared/unresolved-questions.md` |
| Task scope/status change | `tasks/TASK-NNN.json` and `workflow/task_graph.json` |
| Responsibility transfer | `handoffs/` |
| Formal review | `artifacts/reviews/` |
| Short status | `events/events.jsonl` |

Leave a short backlink in the original note so future agents can follow the
thread to the canonical outcome.

## Style

This style applies to all MAP files, not only messages. See
`documentation-style-guide.md`.

Prefer agent-readable structure over prose:

- short headings;
- stable IDs;
- paths;
- bullets;
- tables only when they improve scanning;
- explicit status words such as `open`, `closed`, `pending`, `approved`.

Use complete sentences only when needed to explain a risk, tradeoff, or
unexpected conflict.

## Direct Helper Communication

When a helper talks directly to a non-owning core agent:

1. Give the exchange a thread ID.
2. Record the owning core agent.
3. Keep the question bounded.
4. Copy or summarize the result back to the owner.
5. Promote any scope, ownership, or decision result to the canonical file.

Direct communication is for speed. Promotion is for memory.

## Minimal Inbox Message

For small messages, this is enough:

```md
## MSG-001

- Thread: `THREAD-TASK-048-review-scope`
- Task: `TASK-048`
- Sender: `helper-review-task-048`
- Recipient: `codex`
- Owner: `claude`
- Copied: `claude`
- Requested action: Answer whether `scripts/foo.py` owns the retry behavior.
- Outcome location: pending

Question:

[Specific bounded question.]
```

## Thread Closure

Close a thread when the outcome has been recorded.

Include:

- final answer;
- canonical outcome location;
- remaining follow-up, if any;
- whether the helper or inbox note is still active.

Do not leave important communication only in a helper terminal or chat transcript.
