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
