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
hcom 1 claude --tag helper-review-01 --terminal wezterm-tab --model haiku
```

Claude helpers default to auto permission mode and Haiku. This is a resource
management default, not a capability ceiling. If a helper needs Sonnet or Opus,
the owning agent must first write a short escalation request with the helper
scope, why Haiku is insufficient, the requested tier, and the expected bounded
use. A different core agent reviews that request and chooses the lowest tier
that can reasonably handle the work. Review should be generous when the
reasoning is sound: do not force Haiku onto work that needs stronger reasoning,
and do not spend Sonnet or Opus on tasks Haiku can reliably perform. See
`notes/helper-agent-guide.md` for the tier rubric and request format.

Helper agents are not permanent identities. Each helper must have:

- a stable helper tag like `helper-research-01` or `helper-review-ui`;
- a specific task, question, or review scope;
- a durable note in `MAP_System/inbox/helpers/` describing what it is doing and what it has already learned;
- an owner among the core agents who is accountable for integrating or discarding the helper's output.

Helpers should be stopped when their assigned work is done, stale, duplicated by another helper, or no longer relevant. Do not keep helpers running merely to keep agents busy. Do not allow helpers to bypass task ownership, approval gates, or human approval requirements.

### Routine Reviewer Conflict Routing

If a submitted task needs review, the available reviewer has a no-self-review
conflict, and no clean core reviewer is immediately available, do not ask the
operator to solve the routing problem. Use the existing helper path:

1. Create a durable helper note in `MAP_System/inbox/helpers/`.
2. Spawn a visible temporary review helper with `--terminal wezterm-tab`.
3. Send a bounded review packet naming the task, output paths, conflict reason,
   and required review artifact.
4. Continue tracking the helper and integrate the result through the normal MAP
   review and release gates.

Escalate to the operator only if spawning a visible helper is blocked, the task
needs a human decision, or the review would cross a privacy, destructive-action,
security, or scope boundary.

## Broadcast Coordinator Convention

When an operator or command-center message goes to more than one core agent
at once (a broadcast, e.g. "what did the review find?" or "go fix these
findings"), duplicate ownership is a real risk: two agents can independently
audit the same thing, or both claim the same fix, without either being wrong
to try. This has worked so far only because agents happened to coordinate by
convention (TASK-140/141: claude-lab-vino and codex-lab-neko split a review
broadcast by announcing non-overlapping angles over hcom before starting).
That is not a gate, so it should not be assumed to keep working by luck.

Rule: the first core agent to start substantive work on a broadcast should,
before or immediately as it starts, send the other addressed agent(s) a short
hcom message naming the scope it is claiming (which findings, which files, or
which recommendation number) and inviting a swap if there is a conflict.
`--intent inform` is sufficient; do not block on a reply before starting, but
do stop and re-split if another agent objects or was already mid-work on the
same scope.

If the broadcast is large enough that a full split needs judgment (more than
a couple of independent pieces, or unclear boundaries), the first agent should
propose the split explicitly and wait briefly for the other(s) to confirm or
counter-propose, rather than each agent silently picking a lane. Record the
agreed split in the hcom thread; a durable task file or handoff note is only
required if the resulting work itself needs one under the normal Core
Protocol.

This is deliberately a convention, not new tooling: it targets exactly the
gap TASK-140 found (duplicate-owner risk on broadcasts) without adding a new
process file for something two agents can resolve by talking to each other
first.

## Broad Directive Intake Convention

Broad operator directives should enter MAP through the visible intake wrapper
before an agent decomposes them into tasks or lanes. Default path:

```bash
python3 MAP_System/scripts/command_center_intake.py \
  --hcom-inform-to @bigboss \
  --hcom-name <agent-hcom-name> \
  "operator directive text"
```

The wrapper classifies the directive, validates its own hcom-shaped summary,
optionally posts that summary as `hcom --intent inform`, records the intake
event, and prints the current runner route. This makes the dispatch packet
visible before decomposition without requiring a human approval step.

Urgent live-control messages are exempt: stop/pause/resume instructions,
approval prompts, safety/privacy/scope conflicts, and direct agent routing
messages may be handled immediately through hcom. If the urgent message later
turns into broad implementation work, run intake for the follow-on directive
before creating or splitting tasks.

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

Normal root Git is available from the canonical repo:

```text
/home/home/Projects/MultiAgentProject
```

The canonical repo decision is recorded in `shared/canonical-repo.md` and
`shared/decisions.md` (DEC-014).

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

### Security Second Pass

Any task whose outputs add a network-facing or write-capable component — a
server, listener, endpoint, or anything that can write into the agent bus,
filesystem beyond its own artifacts, or an external service — requires a
second, explicitly security-framed review pass before approval, separate
from the functional review.

The security pass checks trust boundaries specifically: authentication,
CSRF/drive-by exposure, injection, path traversal, identity attribution,
and failure modes on malformed input.

Skip it for purely static, read-only, or documentation work.

Basis: TASK-056's functional review approved a working, input-validated
backend but missed a real CSRF gap that a security-framed second pass then
caught (INS-0004 / IDEA-0004 / PROMO-0004, promoted by TASK-078).
