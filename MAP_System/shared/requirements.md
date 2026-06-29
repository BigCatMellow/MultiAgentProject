<!-- hpom: file: shared/requirements.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: MAP_System audit 2026-06-29 -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Requirements

## Explicit Requirements

- Set up MultiAgentProject for strong communication and collaboration between Codex and Claude Code.
- Include LangGraph-oriented structure and notes because the owner does not yet know how LangGraph should be organized.
- Create folders and notes needed for practical use.

## Operational Requirements

- Use durable files instead of transient chat as project memory.
- Keep task ownership explicit.
- Support independent review.
- Make handoffs readable by both Codex and Claude Code.
- Keep LangGraph as an orchestrator, not the only source of project truth.
- Store canonical project state outside LangGraph. SQLite is now the claim coordinator, and file-backed task records remain the human-readable mirror.
- Route around unavailable agents so session limits do not stall the whole project unless a task explicitly requires that agent.
- Maintain enough current Markdown context for agents to know what is live, what is historical, and how to operate the system safely.

## Current Capabilities

- Autonomous daemon implemented (`scripts/agent_loop.py`, TASK-021): claims, works, and submits tasks in a cyclic LangGraph loop; pauses at `review` and `propose_helper` routes for operator input.

## Non-Goals For This Bootstrap

- No network dependency installation.
- No external API keys or provider configuration.
- No unattended cross-agent process launching. Operator-approved command-center helper launching is allowed when helpers are named, task-scoped, and recorded in durable notes.
- Command-center-launched core agents, helper agents, and assistants must use
  an operator-reachable interface. Visible terminals are the default. Headless
  `hcom` is allowed only when the AI Command Center exposes screen inspection,
  input, approval, and stop controls for that session.
