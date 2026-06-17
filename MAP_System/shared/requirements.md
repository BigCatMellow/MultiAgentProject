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
- Store canonical project state outside LangGraph in files now, with a path to SQLite later.

## Non-Goals For This Bootstrap

- No fully autonomous daemon yet.
- No network dependency installation.
- No external API keys or provider configuration.
- No automatic cross-agent process launching.

