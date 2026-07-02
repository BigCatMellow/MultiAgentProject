<!-- hpom: file: shared/decisions.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: MAP_System audit 2026-06-29 -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Decisions

## DEC-001: Use File-Backed State First

Status: approved
Owner: command-center
Date: 2026-06-17
Applies-To: MAP system — data authority and state storage

Use JSON, Markdown, and JSONL files for the first collaboration layer. This keeps the system inspectable by both Codex and Claude Code before adding SQLite or a service runtime.

## DEC-002: LangGraph Is The Orchestrator

Status: approved
Owner: command-center
Date: 2026-06-17
Applies-To: MAP orchestration layer

LangGraph should route task states, review loops, and human pauses. It should not be the canonical database, artifact store, or full project memory.

## DEC-003: One Owner Per Active Task

Status: approved
Owner: command-center
Date: 2026-06-17
Applies-To: all active tasks

Each active task has one owner. Other agents may review, comment, or continue after a handoff, but should not silently edit the same owned output paths.

## DEC-004: Core Agents Plus Temporary Helpers

Status: approved — core agent list superseded by DEC-008
Owner: command-center
Date: 2026-06-17
Applies-To: agent coordination and helper policy

The command center keeps Codex and Claude as the two active core agents (see DEC-008). Core agents may request or start temporary helper agents for bounded work when parallelism is useful.

Temporary helpers are identified by a `helper-*` tag and documented in `MAP_System/inbox/helpers/`. Helper notes are durable project memory; the helper process itself may be opened, closed, forked, or replaced as needed.

Helper agents do not own final approval. A core agent remains accountable for task ownership, integration, review routing, and cleanup.

## DEC-005: Route Around Unavailable Agents

Status: approved
Owner: command-center
Date: 2026-06-17
Applies-To: agent routing and availability handling

When a core agent reaches a session limit or otherwise becomes unavailable, the system records that state in `MAP_System/agents/status.json`.

Available agents may continue ready work unless a task explicitly declares `required_agent` for the unavailable agent. Work owned by an unavailable agent should be handed off or queued in durable notes before another agent continues.

LangGraph should treat unavailable agents as routing constraints, not as a global stop condition.

## DEC-006: Visible Command-Center Agents

Status: approved
Owner: command-center
Date: 2026-06-17
Applies-To: all agent and helper launches

Command-center launches use an operator-reachable interface for core agents,
temporary helpers, and assistants. Visible terminal tabs are the default.
Headless `hcom` sessions are allowed only when the AI Command Center can
inspect the screen, send input, approve prompts, and stop the session. Hidden
background assistants are disallowed.

For routine in-scope work, agents may use session-level approval options when their tool offers them. This does not remove human approval requirements for destructive actions, external network calls, publication, final release, or changes outside the assigned scope.

## DEC-007: Manual Coordination For Gemini And Antigravity

Status: superseded by DEC-008
Owner: command-center
Date: 2026-06-17
Applies-To: Gemini and Antigravity coordination

Gemini remains in command-center planning state for work the operator chooses to assign manually. Antigravity also may require manual operator prompting until its command-center communication is reliable. Do not assume hcom alone can start or coordinate Gemini or Antigravity work; record ownership and status durably, and let the operator prompt those agents when needed.

## DEC-009: SQLite Is The Task Claiming Coordinator

Status: approved — 2026-06-19
Owner: command-center
Date: 2026-06-19
Applies-To: task claiming — TASK-014 onward

From TASK-014 onward, task claims are made atomically through `MAP_System/map.db` using `MAP_System/db/claims.py`. Agents must not manually edit task JSON files to claim work. The file-backed JSON files remain synchronized as a human-readable mirror of SQLite state, not as the authoritative claim source.

The claim protocol uses `UPDATE ... WHERE rowcount == 1` to guarantee that only one agent can successfully claim a task, even if multiple agents attempt simultaneously. Leases expire after 30 minutes of no heartbeat; `expire_leases()` returns them to READY.

## DEC-008: Codex And Claude Are The Two Active Agents

Status: approved — 2026-06-19
Owner: command-center
Date: 2026-06-19
Applies-To: all task planning and assignment

Gemini and Antigravity are not expected to be available for most of the project (confirmed by operator). Codex and Claude Code are the two active core agents going forward. All task planning, assignment, and workload splitting should assume only these two agents.

Codex handles implementation tasks. Claude handles review, architecture, synthesis, and planning tasks. Both may propose new tasks as work progresses. Temporary helpers remain available when parallelism is needed for a bounded scope.

## DEC-010: STATE_SNAPSHOT Handoff Format

Status: approved — 2026-06-19
Owner: command-center
Date: 2026-06-19
Applies-To: cross-session agent handoffs

Agents should use `STATE_SNAPSHOT` YAML handoff records for cross-session continuity when important context would otherwise live only in chat or a compacted transcript.

The canonical schema and worked example live in `MAP_System/workflow/templates/state_snapshot.yaml`. Snapshots belong in `MAP_System/handoffs/` and should point to durable files instead of copying large context.

Required snapshot coverage: `agent_id`, `session_id`, task context, active constraints, forward tasks, and project-local lexicon. Agents should emit a snapshot before session end when work is active, blocked, or pending review, and should read the latest relevant snapshot on resume before continuing the task.

## DEC-011: HPOM Is The Assignment Layer Over MAP

Status: approved — 2026-06-29
Owner: command-center
Date: 2026-06-29
Applies-To: MAP/HPOM integration and assignment discipline

HPOM means Human-Paced Orchestration Model for this MAP implementation.

MAP remains the durable task, memory, event, and state system. HPOM is the
assignment discipline layered over MAP. It decides whether work should go to
command-center, a core agent, a visible temporary helper, a local assistant, or
Aider based on:

- task clarity;
- authority required;
- model/tool fit;
- visibility and control;
- token and coordination cost.

HPOM does not replace MAP, HCOM, task ownership, review gates, or durable file
memory. It prevents wasteful assignment by requiring a worker-fit reason and a
stop condition before helpers or local assistants are used.

Current references:

- `shared/hpom.md`
- `shared/agent-capability-matrix.md`
- `notes/local-model-helper-guide.md`

Implementation order:

1. Enforce strict task promotion and claim-time metadata defense.
2. Add local assistant health checks.
3. Add local assistant wrappers only after health checks and visibility rules are
   proven.

## DEC-012: Canonical Repo Is Downloads/MultiAgentProject

Status: approved
Owner: command-center (decision authority delegated to core agents via hcom #14454; recorded by claude-lab-rose, TASK-077)
Date: 2026-07-02
Applies-To: repo layout, git operations, cross-repo sync, Pathwell two-repo sync

`/home/home/Downloads/MultiAgentProject` (repo A) is the canonical working
repo. `/home/home/Projects/MultiAgentProject` (repo B) is frozen: no pushes,
no commits, no edits, no sync into or out of it until reconciled.

Basis: the TASK-063 repo-drift audit found B's git HEAD frozen at 2026-06-17
(4 commits behind A) while its working tree was manually overwritten with
newer uncommitted files — a hybrid state that would produce corrupt-looking
history if committed or pushed. All current validated work happened in A.

Reconciliation plan (in order, after TASK-065's git-operation lock exists):

1. Preserve B's `Projects/Pathwell/` and `Projects/Backups/` before anything
   else. These are gitignored private content and exist in B only as working
   files; a reclone or clean would delete them. They are stale relative to A
   but are the only copy of that private work outside A.
2. Single clean commit in A covering the audited/validated state (after the
   TASK-065 remediation batch lands and all validators pass).
3. Push A to `origin` — operator-visible step; announce via hcom first.
4. Reset or reclone B from the remote, then restore/refresh its private
   `Projects/Pathwell/` copy from A via file sync (not git).
5. Resume the Pathwell two-repo sync protocol only after steps 1-4 complete.

Until step 4 completes, a freeze marker should be placed in B
(deferred at codex-lab-limo's request until the git lock tooling exists).
