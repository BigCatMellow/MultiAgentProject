# Communication Guide

This guide defines how core agents, helper agents, and assistants should talk to
each other in MAP.

## Principle

Communication should be direct enough to avoid bottlenecks, but accountable
enough that ownership does not get lost.

Helpers may ask another core agent a bounded question directly. They should not
silently transfer ownership, change task scope, or make final decisions without
their owning core agent.

## Agent Roles

### Core Agents

Core agents can own tasks, integrate work, request reviews, approve work they
did not author, and create helpers.

Current core agents:

- Codex
- Claude Code

### Helper Agents

Helpers are temporary scoped workers. A helper has an owning core agent.

Helpers can:

- inspect files;
- produce notes or artifacts;
- ask bounded questions;
- provide independent review or research.

Helpers cannot:

- approve final deliverables;
- change task ownership by themselves;
- expand scope without owner approval;
- bypass human approval gates;
- coordinate indefinitely without a stop condition.

## Preferred Communication Paths

```text
core agent -> core agent
  Use handoff, review artifact, inbox note, or event.

helper -> owning core agent
  Default path for findings, blockers, and scope questions.

helper -> other core agent
  Allowed for bounded factual questions or review requests.
  Copy or summarize back to the owning core agent.

helper -> helper
  Avoid unless both helpers have the same owner and the scope is narrow.
  Record the exchange in the helper notes.

core agent -> helper owned by another core agent
  Allowed for bounded questions.
  Notify the helper owner if it changes priority, scope, or conclusions.
```

## Direct Contact Rule

A Claude-created helper may talk directly to Codex when:

- the question is narrow;
- the answer will not change task ownership;
- the exchange is recorded in `inbox/helpers/`, `inbox/codex/`, or an event;
- Claude remains accountable for integrating the helper's findings.

Route through Claude instead when:

- the request changes task scope;
- the helper needs a new assignment;
- the decision affects ownership, priority, or approval;
- the helper is asking Codex to do implementation work;
- the question could conflict with Claude's current plan.

The same rule applies in reverse for Codex-created helpers talking to Claude.

## Message Types

Use the lightest durable channel that fits:

- `events/events.jsonl` - short factual status updates.
- `inbox/<agent>/` - scoped note to a specific agent.
- `inbox/helpers/` - helper scope, findings, and cross-helper notes.
- `handoffs/` - transfer of responsibility or continuation context.
- `artifacts/reviews/` - formal review result.
- `shared/decisions.md` - approved durable decision.
- `shared/unresolved-questions.md` - open question needing project-level decision.

## Message Shape

For inbox or helper notes, include:

- sender;
- intended recipient;
- task or scope;
- question or finding;
- requested action;
- deadline or urgency if any;
- whether the owning core agent was copied.

For any exchange that may need follow-up, use a thread ID and message IDs. See
`communication-architecture.md` for the traceability model and
`templates/inbox-message.md` for a reusable message shape.

## Escalation

Escalate to the owning core agent or human operator when:

- two agents disagree on scope;
- a helper receives conflicting instructions;
- approval is needed;
- a destructive or external action is proposed;
- the communication path itself becomes unclear.

## Anti-Patterns

Avoid:

- helpers making final decisions;
- unrecorded side conversations;
- asking multiple agents the same broad question without assigning ownership;
- routing every small question through the owner when direct contact would be faster;
- letting direct helper-to-core communication become a hidden task transfer.
