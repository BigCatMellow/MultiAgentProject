# Agent Availability

`status.json` is the durable availability board for core command-center agents and manually coordinated agents.

Use it when an agent hits a session limit, has approval pending, is offline, or is otherwise unavailable. The command center and LangGraph runner should route around unavailable agents unless a task explicitly requires that agent.

Gemini and Antigravity may require manual operator prompting. Keep them in the plan when useful, but do not assume hcom communication alone is enough to start or coordinate their work.

Supported statuses:

- `available`: agent can receive new work;
- `busy`: agent is online but should not receive new work yet;
- `standby`: agent is unavailable until a known or approximate resume time;
- `offline`: agent is unavailable with no known resume time.

Tasks can opt into a hard requirement for a specific agent by adding:

```json
"required_agent": "gemini"
```

If the required agent is unavailable, LangGraph routes to `wait_for_agent`. Otherwise, ready work can continue with available core agents, and notes for the unavailable agent should be queued in its inbox or a handoff file.
