<!-- hpom: file: shared/hpom.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: MAP_System audit 2026-06-29 -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# HPOM - Human-Paced Orchestration Model

Status: working definition
Decision: DEC-011
Owner: command-center

## Purpose

HPOM is the assignment and escalation layer above MAP.

MAP answers:

- What is the task?
- Who owns it?
- What files are canonical?
- What state is it in?
- What got decided?

HPOM answers:

- Who or what should do this kind of work?
- Is this safe for a local assistant?
- Does this need a paid/core agent?
- Does this need human intent or approval first?
- Would a helper add value, or just burn tokens?

## Principle

Use the cheapest competent worker, but keep authority with the right owner.

Cheap means lower token cost, lower interruption cost, lower coordination cost,
and lower risk. Competent means the worker is actually good at the task shape.

Do not assign work to a model or helper just because it is available.

## Authority Tiers

| Tier | Worker | Authority | Use For | Do Not Use For |
|---|---|---|---|---|
| 0 | command-center / human | final intent and priority | goals, approvals, product direction, broad tradeoffs | routine file inspection |
| 1 | core agents: Codex, Claude | task ownership and final integration | implementation, architecture, review, durable synthesis | approving own work |
| 2 | visible temporary helpers | scoped support | bounded review, research, inspection, alternate draft | ownership transfer, hidden background work |
| 3 | local assistants / Ollama | draft-only support | summaries, classification, JSON checks, checklist passes, small suggestions | final decisions, broad rewrites |
| 4 | Aider with local model | supervised edit-helper | narrow named-file edits after baseline checks | broad refactors, ambiguous edits |

## Routing Questions

Before assigning work, answer these in order:

1. Is the task intent clear enough to write pass/fail acceptance criteria?
2. Does the task require final judgment, architecture, security, or user intent?
3. Is there a narrow read/check/draft portion that a local assistant can do?
4. Would a helper reduce wall-clock time enough to justify coordination cost?
5. Are the helper's output paths and stop condition explicit?
6. Is the session visible or otherwise reachable by command-center controls?

If the answer to question 1 is no, use the Architect/Shaper path. Do not give
the task to an execution helper.

## Default Assignment Rules

- Codex: repository edits, scripts, tests, validators, SQLite/task-state logic,
  command-center CLI work, implementation plans with concrete files.
- Claude: independent review, architecture critique, prose-heavy synthesis,
  task shaping, risks, acceptance criteria, operator-facing summaries.
- Local summarizer models: event digests, current-state summaries, task
  classification, question extraction.
- Local coder models: task JSON checks, schema checks, small validator drafts,
  narrow diff suggestions.
- Aider: named-file supervised coding after Git and output-path checks.
- Gemini / Antigravity: manual or standby specialist helpers only when the
  operator activates them and the work fits their strengths.

## Escalation Rules

Escalate from local assistant to core agent when:

- output would change MAP state;
- the assistant reports uncertainty;
- architecture or policy judgment is required;
- the task affects approval gates, task claims, or helper routing;
- the result will be treated as final by another worker.

Escalate from core agent to command-center when:

- task intent is ambiguous;
- HPOM/MAP boundaries would change;
- destructive, external, publication, or broad Git actions are needed;
- a human preference or priority decides the result.

## Recording Requirements

When HPOM assigns work, record:

- worker or tool;
- owner;
- task id or reason;
- scope;
- input paths;
- output or recommendation path;
- stop condition;
- final integration owner.

Use:

- `tasks/` for owned task work;
- `inbox/helpers/` for helper notes;
- `artifacts/planning/` for routing plans;
- `shared/decisions.md` for approved assignment policy;
- `events/events.jsonl` for short activity records.

## Local Assistant Policy

Local assistants are helper capabilities, not core agents.

They may produce:

- `summary`
- `classification`
- `checklist-result`
- `draft`
- `recommendation`
- `diff-suggestion`

They may not produce:

- final approval;
- final architecture decisions;
- task completion claims;
- broad rewrites;
- hidden background work.

## Implementation Sequence

1. Enforce strict READY promotion (`TASK-035`).
2. Add local assistant health checks (`TASK-036`).
3. Keep this HPOM spec and `agent-capability-matrix.md` current as agent/tool
   behavior is proven.
4. Add command-center wrappers only after manual health checks and visibility
   rules are proven.

## Open Edges

- HPOM name can be renamed if command-center intended a different expansion.
- Gemini and Antigravity strengths should be updated only from successful
  observed use, not assumptions.
- Local assistant wrappers should stay read-only until health checks exist.
