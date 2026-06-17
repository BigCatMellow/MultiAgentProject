# Pathwell Requirements

## Explicit Requirements

- Use MAP inside the Pathwell folder so the story project can be worked on directly.
- Preserve the current story files under `Pathwell/Story_Files/`.
- Let Codex and Claude Code collaborate through tasks, handoffs, reviews, and durable artifacts.

## Operational Requirements

- Use durable files instead of transient chat as project memory.
- Keep task ownership explicit.
- Support independent review.
- Make handoffs readable by both Codex and Claude Code.
- Keep LangGraph as an orchestrator, not the only source of project truth.
- Store canonical project state outside LangGraph in files now, with a path to SQLite later.
- For story work, cite the relevant source file and section whenever making structural claims.
- Separate canon facts from suggestions, hypotheses, and open questions.

## Non-Goals For This Bootstrap

- No fully autonomous daemon yet.
- No network dependency installation.
- No external API keys or provider configuration.
- No automatic cross-agent process launching.
