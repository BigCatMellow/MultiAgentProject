<!-- hpom: file: shared/architecture.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: MAP_System audit 2026-06-29 -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Architecture

MAP is a file-first multi-agent coordination system with SQLite-backed task
claiming and LangGraph orchestration.

## Responsibilities

```text
Markdown and JSON files  Durable memory and inspectable project truth
SQLite                   Atomic task claims, leases, events, and runtime state
LangGraph                Routing, review gates, human pauses, and next actions
Scripts                  Operator tools, validation, tests, and reconciliation
Agents                   Task execution, review, planning, and handoffs
```

## Local Helper Capabilities

Local Ollama models and Aider can support low-risk summarizing, JSON checking,
markdown cleanup, validation-script drafting, and narrow supervised edits.

They are helper capabilities, not final authorities and not core agents by
default. See `notes/local-model-helper-guide.md`.

Authority split:

- paid/core agents own judgment, task accountability, and final decisions;
- local assistants reduce paid-model load through summaries, checks, drafts,
  recommendations, and narrow diff suggestions;
- local assistant output must be reviewed before it changes MAP state.

## HPOM

HPOM, the Human-Paced Orchestration Model, is the assignment discipline layered
over MAP. MAP stores durable task state and coordination truth; HPOM decides
which worker type should handle each piece of work based on risk, authority,
model fit, visibility, and token cost.

See `shared/hpom.md` and `shared/agent-capability-matrix.md`.

## File Memory

Files are the readable project brain:

- `shared/` stores current truth.
- `tasks/` stores task records.
- `workflow/task_graph.json` stores the file-backed task graph mirror.
- `artifacts/` stores historical work products.
- `handoffs/` stores cross-session continuity.
- `events/events.jsonl` stores append-only activity records.

## SQLite

`map.db` coordinates mutable runtime state that benefits from atomic operations.

Primary responsibilities:

- task claims;
- leases and heartbeats;
- task submission state;
- approval gates;
- event records.

Task files remain the human-readable mirror. Agents should not manually edit
task JSON to claim work.

## State Machine Guardrails

Task execution should be protected by a strict state machine:

```text
BACKLOG -> NEEDS_SHAPING -> READY -> IN_PROGRESS -> SUBMITTED -> APPROVED
```

Only metadata-complete tasks should enter `READY`. See
`notes/state-machine-guardrails.md`.

Raw ideas or incomplete task records should be shaped by the Architect/Shaper
role before execution. See `notes/architect-agent-guide.md`.

## LangGraph

`graph/runner.py` uses LangGraph to inspect current state and choose the next
route. It can route toward review, helper proposal, ready work, wait states, or
reconciliation.

LangGraph is the orchestrator. It is not the canonical long-term memory.

## Agent Loop

`scripts/agent_loop.py` runs cyclic task claiming and handling. It can pause at
operator-required gates and uses lock files to avoid duplicate loops for the
same agent/database pair.

Handler commands are trusted operator configuration.

## Synchronization

The system currently keeps both SQLite and file mirrors. When task state changes,
agents or scripts must synchronize:

- `tasks/TASK-NNN.json`
- `workflow/task_graph.json`
- relevant SQLite rows
- `events/events.jsonl`

Use existing scripts where possible instead of hand-editing state in multiple
places.
