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

## hcom Message Intent (TASK-202)

hcom messages **may** carry an `intent` (`request` | `inform` | `ack`) —
agents should set one on every send (see this file's Style/promotion rules
for the underlying discipline), but it is not guaranteed present: the
real-world measurement in `map-real-parameter-calibration-results-2026-07-14.md`
found roughly half of agent messages and nearly all operator messages have
no `intent` set. Any code or query that consumes hcom intent must handle
`None`/unset explicitly rather than assuming every message has one.
Separately, and regardless of whether intent is set, **hcom intent is not
durable MAP state.** It lives only inside hcom's own
SQLite store (queried via the `hcom events` CLI's `events_v` view,
`msg_intent` column), not in `events/events.jsonl` and not in
`runtime/session_replay.sqlite` — `scripts/session_replay.py` does not
ingest hcom at all (zero hcom references in that file, confirmed by TASK-202;
an earlier work packet had assumed otherwise). This is a deliberate
boundary, not a gap: hcom already owns and indexes its own message store,
and MAP's disposable replay index intentionally covers only MAP-canonical
sources (`events.jsonl`, task JSON/SQLite mirrors).

**Do not backfill or bridge hcom's message history into
`session_replay.sqlite`.** If a measurement needs hcom intent, query hcom
directly and join by timestamp/agent to MAP's own event/task data in the
measurement script itself — keep the two stores separate and query them
independently rather than duplicating one into the other.

Runnable query example (used as the parameter-7/P1-practice smoke test in
`artifacts/audits/map-real-parameter-calibration-results-2026-07-14.md`):

```bash
# All request-intent messages, most recent first
hcom events --last 5000 --type message --intent request --name <your-name>

# Raw SQL form (same events_v view), e.g. messages from an operator identity
hcom events --last 5000 --sql "type='message' AND msg_from='command-center'" --name <your-name>
```

Both return JSON lines shaped `{"data": {"from": ..., "intent": ..., "text":
...}, "id": ..., "instance": ..., "ts": ..., "type": "message"}` — the
`--sql` form's WHERE clause uses the underlying `events_v` column names
(`msg_from`, `msg_intent`, `msg_scope`, `msg_thread`), but the JSON result
still surfaces them as `data.from`/`data.intent`. Join on `data.from`/`ts`
against `agents/operator-identities.json` and MAP task/event timestamps for
operator-load or intent-mix measurements.
