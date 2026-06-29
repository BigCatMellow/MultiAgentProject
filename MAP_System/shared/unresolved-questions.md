<!-- hpom: file: shared/unresolved-questions.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: MAP_System audit 2026-06-29 -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Unresolved Questions

## Open

- Should Codex and Claude Code use separate branches/worktrees once Git is initialized correctly?
- What model/provider should the future LangGraph runtime call for each role?
- Should the first real workflow target writing, software, research, or general project management?

## Resolved

- **Should the next version use SQLite for atomic claims and leases?** → Yes. See DEC-009. Implemented in `db/claims.py` (TASK-014).
- **Should a fully autonomous daemon claim and work tasks without operator intervention?** → Yes, with operator interrupt gates for `review` and `propose_helper` routes. Implemented in `scripts/agent_loop.py` (TASK-021).
- **Should Gemini and Antigravity be treated as active core agents?** → No. See DEC-008. Codex and Claude are the two active core agents.
