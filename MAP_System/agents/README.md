# Agent Availability

`status.json` is the durable availability board for core command-center agents and manually coordinated agents.

Use it when an agent hits a session limit, has approval pending, is offline, or is otherwise unavailable. The command center and LangGraph runner should route around unavailable agents unless a task explicitly requires that agent.

## Identity kinds (F6 semantics, reconciled 2026-07-02, TASK-082)

The file mixes three kinds of identity. Read it with these rules:

- **Live session agents** (`claude-lab-*`, `codex-lab-*`, `codex-live`, ...):
  one hcom session each. `available` means live *as of the last reconcile* —
  `hcom list` is always the live authority; this file is the durable record.
  Ended sessions are `inactive` / `session_ended` and can be resumed with
  `hcom r <name>` if their context is needed.
- **Capability identities** (`claude`, `codex`): the core agent *types*
  (DEC-008). Always `available` while the capability exists; never a live
  session.
- **Human / relay identities**: `bigboss` is the operator. `antigravity` is
  reachable only by asking the operator to prompt it
  (`reason: operator_relay_only`).
- **Tool artifacts** (`map-task`): side effects of `map_task.py
  ensure_agent()`; not agents (`inactive` / `tool_identity`).

## Field conventions

- `status`: `available` | `busy` | `standby` | `inactive` | `offline`
- `reason`: `out_of_tokens` | `session_ended` | `long_term_unavailable` |
  `operator_relay_only` | `tool_identity` | null
- `resume_after`: must be an **ISO-8601 timestamp** when `reason` is
  `out_of_tokens` — the limit watcher (`scripts/limit_watcher.py`, TASK-080)
  auto-resumes agents from it and flags free text as unparseable rather than
  guessing. See `notes/limit-exhaustion-protocol.md`.

## Maintenance

- Reconcile against live reality:
  `hcom list --json > /tmp/live.json && python3 MAP_System/scripts/reconcile_agents.py --hcom-json /tmp/live.json`
- Agents update their own entry at limit time per the limit-exhaustion
  protocol; the watcher and reconcile report catch what they miss.
- Do not route work from this file alone; check hcom first
  (`shared/approval-calibration.md`).

## Hard agent requirements

Tasks can opt into a hard requirement for a specific agent by adding:

```json
"required_agent": "gemini"
```

If the required agent is unavailable, LangGraph routes to `wait_for_agent`. Otherwise, ready work can continue with available core agents, and notes for the unavailable agent should be queued in its inbox or a handoff file.
