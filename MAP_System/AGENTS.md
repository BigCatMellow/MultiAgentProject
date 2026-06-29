# Agent Operating Rules

These rules apply to Codex, Claude Code, and any future worker agent in this workspace.

## Core Protocol

1. Work only on an assigned or explicitly claimed task from `tasks/`.
2. Read `shared/project-brief.md`, `shared/requirements.md`, `shared/decisions.md`, and the task file before editing.
3. Keep one accountable owner per active task.
4. Do not silently modify another active task's owned output paths.
5. Record important assumptions in `shared/unresolved-questions.md` or `shared/decisions.md`.
6. Put durable work in `artifacts/`, `shared/`, `workflow/`, `tasks/`, or source files, not only in chat.
7. Use `events/events.jsonl` for short append-only activity records.
8. Use `handoffs/` for work that another agent should review or continue.
9. Do not approve your own substantive deliverable.
10. Stop when the task acceptance criteria are met.

## Documentation Style

All MAP Markdown and template files should be agent-readable first. Prefer
structured fields, stable IDs, explicit statuses, file paths, task IDs, and
bullets over prose narrative.

Use complete sentences when explaining risk, tradeoff, exception, conflict, or
decision reasoning. For normal state, use compact structure.

See `notes/documentation-style-guide.md`.

## Pushback Standard

Agents should push back when a request or proposed design would make MAP more
fragile, ambiguous, expensive to read, or unsafe.

Push back especially on:

- over-design before current validation failures are fixed;
- adding new files that do not change agent behavior;
- database triggers before script-level gates are proven;
- self-healing flows that silently invent task intent;
- helper communication that bypasses ownership;
- compaction that deletes raw history instead of summarizing forward;
- changes that hide task ownership, status, output paths, or acceptance criteria.

When pushing back:

- name the concrete risk;
- propose the safer alternative;
- keep the user's goal as the anchor;
- continue with the safe portion when possible.

## Task Claiming (SQLite)

As of TASK-014, task claims are coordinated through `MAP_System/map.db` using the atomic claim module at `MAP_System/db/claims.py`. Do not edit task JSON files directly to claim work.

**Claiming a task:**

```python
from MAP_System.db.claims import claim_task, heartbeat, submit_task, expire_leases

success = claim_task("TASK-NNN", "your-agent-id")   # returns False if already claimed
```

**While working** (renew every ~15 minutes to avoid lease expiration):

```python
heartbeat("TASK-NNN", "your-agent-id")
```

**When done:**

```python
submit_task("TASK-NNN", "your-agent-id")   # sets status to SUBMITTED, clears lease
```

**Reconciliation** (run by the LangGraph runner or manually):

```python
expired = expire_leases()   # returns tasks back to READY when lease has passed
```

Update `workflow/task_graph.json` and the task's individual JSON file to reflect the new status after claiming or submitting, so the file-backed state stays synchronized with SQLite.

## Elastic Helper Agents

The command center keeps Codex and Claude as the two active core agents (see DEC-008). Core agents may start temporary helper agents when a task benefits from parallel research, review, implementation, or focused analysis.

**Spawning helpers:** use a command-center-managed terminal surface. A visible
terminal tab is the default. Headless `hcom` is allowed only when the AI Command
Center can inspect the screen, send input, approve prompts, and stop the
session through commands such as `ai screen`, `ai helper send`, `ai approve`,
and `ai helper stop`.

Do not run assistants in an unreachable background mode.

```bash
hcom 1 claude --tag helper-review-01 --terminal wezterm-tab
```

Helper agents are not permanent identities. Each helper must have:

- a stable helper tag like `helper-research-01` or `helper-review-ui`;
- a specific task, question, or review scope;
- a durable note in `MAP_System/inbox/helpers/` describing what it is doing and what it has already learned;
- an owner among the core agents who is accountable for integrating or discarding the helper's output.

Helpers should be stopped when their assigned work is done, stale, duplicated by another helper, or no longer relevant. Do not keep helpers running merely to keep agents busy. Do not allow helpers to bypass task ownership, approval gates, or human approval requirements.

## Autonomous Claim Loop

An autonomous task daemon is available at `MAP_System/scripts/agent_loop.py`. It claims, works, and submits tasks in a cyclic LangGraph loop without operator intervention for normal work. It pauses at `review` and `propose_helper` routes, requiring operator input before resuming.

```bash
MAP_System/.venv/bin/python MAP_System/scripts/agent_loop.py \
  --agent-id codex \
  --handler "python3 MAP_System/scripts/handle_task.py {task_id}" \
  --heartbeat-interval 300 \
  --lease-seconds 1800
```

Use `--once` for a single-cycle run. Use `--dry-run` to verify routing without claiming. The loop acquires a per-agent-id lockfile at startup and releases it on exit or SIGTERM.

## Agent Availability And Session Limits

Agent availability is durable project state. When an agent reaches a session limit, is waiting for approval, goes offline, or otherwise cannot work, record it in `MAP_System/agents/status.json`.

Other agents should continue with available work unless a task explicitly requires the unavailable agent. If work was owned by an unavailable agent, create a handoff or queue a note before another agent continues. Do not wait for an unavailable agent merely because it was previously participating.

Use `required_agent` in a task only when that exact agent is necessary. Otherwise, tasks should be transferable among available core agents or temporary helpers.

## Git Protocol

Normal root Git is available at `/home/home/Downloads/MultiAgentProject`.

Remote:

```text
https://github.com/BigCatMellow/MultiAgentProject.git
```

Use normal Git or the compatibility wrapper:

```bash
git status
MAP_System/scripts/map-git status
```

The wrapper delegates to root Git and exists so older MAP instructions still
work.

See `notes/git-setup.md` for details.

## Communication

Use MATOCP tokens for agent-to-agent messages (see `phatic-suppression.md`):

| Token | Meaning |
|---|---|
| `!ACK [id]` | Acknowledged, proceeding |
| `!LGTM` | Approved, no issues |
| `!ERR [code] reason="..."` | Failed, reason given |
| `!REQ key context="..."` | Need this before continuing |
| `!WARN [code] reason="..."` | Flag, not blocking |
| `!NOTE [text ≤200 chars]` | Anything that doesn't fit a token |

For longer structured events, prefer these types in `events/events.jsonl`:

- `PROGRESS`, `SUBMISSION`, `REVIEW_REQUESTED`, `CHANGES_REQUESTED`, `APPROVED`
- `QUESTION`, `ANSWER`, `BLOCKED`, `HANDOFF`
- `DECISION_PROPOSED`, `DECISION_RECORDED`

Use this compact event shape in `events/events.jsonl`:

```json
{"created_at":"2026-06-17T00:00:00-04:00","type":"PROGRESS","task_id":"TASK-001","sender":"codex","summary":"Short factual update","artifact_paths":[]}
```

## Handoff Format

Create a Markdown file in `handoffs/` named like:

```text
HANDOFF-TASK-001-codex-to-claude.md
```

Include:

- task ID
- sender
- intended recipient
- status
- files changed or created
- what needs review or continuation
- known limitations

## STATE_SNAPSHOT Resume Format

Use `STATE_SNAPSHOT` YAML when a session ends with active work, blocked work, or pending review state that the next agent should not re-derive from scratch. The schema and example live at `MAP_System/workflow/templates/state_snapshot.yaml`.

Emit snapshots in `MAP_System/handoffs/` with names like:

```text
STATE_SNAPSHOT-codex-20260619T104500.yaml
```

Before resuming a task, check `MAP_System/handoffs/` for the latest relevant `STATE_SNAPSHOT-*` file from the previous owner or reviewer. Load it as orientation only; SQLite task state, task files, decisions, and artifacts remain canonical.

## File Ownership

Task files list `output_paths`. Treat those as owned by the task while it is active. If ownership needs to change, create a handoff and update the task status.

## Review Standard

Review findings should be concrete and actionable. Use severities:

- `BLOCKER`
- `REQUIRED`
- `RECOMMENDED`
- `OPTIONAL`

Only `BLOCKER` and `REQUIRED` findings should block approval.
