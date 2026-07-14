# Helper Agent Guide

Temporary helper agents are useful for bounded parallel work. They should not
become unmanaged background workers.

## When To Use A Helper

Use a helper for:

- independent review;
- focused research;
- repetitive inspection across many files;
- implementation support with clear ownership;
- summarizing a large but bounded context set.

Do not use a helper just to keep agents busy.

Local Ollama models and Aider may be used as helper capabilities for low-risk
support work. See `local-model-helper-guide.md`.

Use local assistants to reduce paid-model load, not to replace core-agent
ownership. Expected outputs are summaries, classifications, checklist results,
drafts, recommendations, or diff suggestions.

### Review-Conflict Default

When a submitted task needs review and the obvious live reviewer has a
no-self-review conflict, the owning agent should route to a visible helper
without asking the operator, provided the review is routine and bounded.

Default sequence:

1. Record the conflict in `events/events.jsonl` or the task timeline.
2. Create `inbox/helpers/helper-review-task-NNN.md` with owner, scope, input
   paths, conflict reason, expected review artifact, and stop condition.
3. Spawn a visible helper:

   ```bash
   hcom 1 claude --tag helper-review-task-NNN --terminal wezterm-tab
   ```

4. Send the helper a bounded review packet.
5. Validate the helper's review artifact before release.
6. Stop or retire the helper after its findings are integrated.

Ask the operator only when helper spawning is unavailable, the task requires a
human decision, or the review crosses privacy, destructive-action, security, or
scope boundaries.

## Broadcast Ownership (Core Agents, Not Helpers)

This guide is about spawning and running helpers. A related but separate
problem is two *core* agents (Claude, Codex, or their lab sessions) both
responding to the same operator broadcast — that is not a helper-routing
question and is covered in `AGENTS.md` under "Broadcast Coordinator
Convention": the first agent to act announces its claimed scope over hcom
before starting, instead of both agents independently duplicating the same
audit or fix.

## Required Setup

Every helper needs:

- a stable tag, such as `helper-review-task-048`;
- a specific scope;
- an owning core agent;
- command-center-managed terminal mode;
- a durable note in `inbox/helpers/`.

Visible terminal tabs are the default. Headless `hcom` is allowed only when the
AI Command Center remains the operator interface for inspecting screen state,
sending input, approving prompts, and stopping the helper.

Do not run assistants or helper agents in an unreachable background mode.

Example:

```bash
hcom 1 claude --tag helper-review-task-048 --terminal wezterm-tab
```

## Permission Mode For Claude Helpers

For bounded, low-risk Claude helper work, the owning core agent may put the
helper into the least-interruptive permission mode available in the visible
terminal after spawn, then verify the screen state with `hcom term`.

Allowed cases:

- read-only review;
- bounded file inspection;
- local syntax or validator commands already inside the task scope;
- draft-only findings that the core owner will integrate.

Do not use an auto-approval mode for work that crosses a human approval,
privacy/scope, security, destructive-action, external-service, broad Git, or
publication boundary. In those cases the helper should remain interruptible and
the owning core agent should escalate through the normal operator request
format.

Record the chosen permission mode, verification method, and stop condition in
the helper note when the setting materially affects whether the helper can
finish without waiting on the operator.

## Helper Note

Create or update:

```text
inbox/helpers/helper-review-task-048.md
```

Include:

- helper tag;
- tool or provider;
- owner;
- task or question;
- input paths;
- findings;
- current status;
- stop condition.

## Stop Conditions

Stop or retire a helper when:

- its assigned work is complete;
- its findings have been integrated or rejected;
- it is stale;
- another helper duplicates the same scope;
- it is waiting indefinitely on unavailable context.

## Accountability

The owning core agent remains responsible for final integration, review routing,
and cleanup. Helpers do not approve final deliverables.

Local assistants do not claim completion, approve reviews, or make final
architecture decisions.

## Communication

Helpers should report findings to their owning core agent by default.

Direct helper-to-core communication is allowed for bounded questions. For
example, a Claude-owned helper may ask Codex a narrow implementation question
directly, but it must record the exchange and summarize it back to Claude.

Route communication through the owning core agent when the request changes task
scope, ownership, priority, implementation responsibility, or approval state.

See `communication-guide.md` for the full routing rules.
