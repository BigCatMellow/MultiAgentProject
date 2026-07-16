<!-- hpom: file: shared/decisions.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: DEC-028 proving-workflow direction (operator) -->
<!-- hpom: verified_against_prior: MAP_System audit 2026-06-29 -->
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
Supersedes: DEC-004, DEC-007

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

Status: superseded by DEC-014
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

Supersession note, 2026-07-02: TASK-079 completed the reconciliation sequence.
Later live lab sessions and authorized pushes moved to
`/home/home/Projects/MultiAgentProject`. DEC-014 supersedes DEC-012's
path-specific canonical repo rule.

## DEC-013: Synthesis And Experiment Record Types Stay Active, Not Mandatory

Status: approved
Owner: command-center (decision delegated via hcom #15008; recorded by claude-lab-rose, TASK-082)
Date: 2026-07-02
Applies-To: emergence system usage

Report Phase 2.4 asked whether the never-used synthesis and experiment
emergence types should be kept, tested, or marked advanced/optional.

Decision: both stay active and first-class, used only when genuinely
warranted — never as ceremony. A synthesis is warranted when multiple
insights turn out to share one deeper pattern (first real use: SYN-0001,
"two readers, one truth," drawn from six of this week's incidents). An
experiment is warranted when a claim is testable before being promoted
(none yet; the next candidate should use it rather than promoting untested).
`map_emergence.py stale` treats absence of SYN/EXP records as normal, not
as debt.

## DEC-014: Canonical Repo Is Projects/MultiAgentProject

Status: approved
Owner: command-center (operator confirmation via hcom #17759; recorded by codex-lab-limo, TASK-090)
Date: 2026-07-02
Applies-To: repo layout, git operations, command-center lab sessions, RnS watcher state
Supersedes: DEC-012

`/home/home/Projects/MultiAgentProject` is the canonical working repo for
current MAP work.

Basis:

- TASK-079 completed the DEC-012 reconciliation plan.
- The previous canonical path, `/home/home/Downloads/MultiAgentProject`, is no
  longer the live command-center working path.
- Current lab sessions, task state, CommandCenterUI work, RnS watcher runtime,
  and recent authorized pushes are operating from
  `/home/home/Projects/MultiAgentProject`.
- Operator hcom #17759 instructed agents to stop waiting and continue work when
  work remains; Zaro explicitly confirmed in hcom #17774 that TASK-090 should
  treat #17759 as canonical-repo confirmation, with operator veto available on
  review.

Effect:

- `MAP_System/shared/canonical-repo.md` now names
  `/home/home/Projects/MultiAgentProject` as canonical.
- The old Downloads path is retired/non-authoritative if it reappears.
- Normal task-scoped commits and pushes may proceed from the Projects repo when
  owned paths are staged, validators pass, and MAP review/release gates are
  followed.
- Repository-global operations still require the git operation lock.

## DEC-015: Adopt the MAP Research System

Status: approved
Owner: command-center (directed via hcom #19306; built by claude-lab-valo, TASK-103)
Date: 2026-07-03
Applies-To: knowledge acquisition, research artifacts, decisions fed by research

`MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md` identified the Research System as
the highest-priority missing MAP system: MAP could move work safely and
capture ideas safely, but had no formal process for establishing that a
claim is true, current, and sourced before it became project truth.

Effect:

- `MAP_System/RESEARCH_SYSTEM.md` defines the research flow: Research
  Question → Research Brief → Source Map → Source Evaluation → Claim
  Evidence Matrix → Assumption Register → Research Summary → Decision or
  HPOM Task.
- `MAP_System/research/README.md` is the working quick-start.
- `MAP_System/templates/research/` holds the six research templates.
- Research conclusions that change project truth are still recorded as
  normal `DEC-NNN` entries here; the Research System does not bypass the
  decision log or HPOM review/release gates.
- Unsourced claims used in tasks or decisions must be logged in an
  Assumption Register, not silently absorbed into architecture.

## DEC-016: Adopt the MAP Self-Repair System

Status: approved
Owner: command-center (directed via hcom #19306/#19718; built by claude-lab-valo, TASK-105)
Date: 2026-07-03
Applies-To: repair behavior across MAP validators, reconciliation, and health checks

`MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md` identified Self-Repair as gap
#2: MAP already had repair behavior (validators, `reconcile_agents.py`,
`map_emergence.py stale`, `map_metrics.py`, `local_assistant_health.py`,
`test_exporter_invariants.py`) but no formal module tying it together.

Effect:

- `MAP_System/SELF_REPAIR_SYSTEM.md` defines repair severity levels
  (COSMETIC/DRIFT/BLOCKING/STRUCTURAL), automatic-repair permissions by
  HPOM tier, escalation rules, verification plans, and follow-up
  prevention.
- `MAP_System/repairs/README.md` is the working quick-start.
- `MAP_System/templates/repairs/` holds the Repair Record and Health Check
  Report templates.
- STRUCTURAL repairs still require command-center approval or a normal
  decision entry — Self-Repair does not grant agents new unilateral
  authority.
- Cross-linked to the Research System (DEC-015): stale/contradictory facts
  identified by research are DRIFT/BLOCKING repair targets here. Cross-
  linked to Emergence: recurring repairs should be captured as insights
  and promoted into permanent validator/template/decision fixes.

## DEC-017: Adopt the MAP Context System

Status: approved
Owner: command-center (directed via hcom #19306/#19718; built by claude-lab-valo, TASK-107)
Date: 2026-07-03
Applies-To: context assembly for tasks, reviews, research, and repairs

`MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md` identified the Context System
as gap #3: `notes/context-routing-guide.md` and `shared/memory-map.md`
already define what to read and in what order, but context itself was not
formalized as a bounded packet with required/optional/forbidden content,
staleness handling, token-budget rules, and a local-summarizer boundary.

Effect:

- `MAP_System/CONTEXT_SYSTEM.md` defines the context packet format,
  required context by task type, forbidden context loading, stale-context
  handling (as a Self-Repair DRIFT target), token-budget rules, the
  local-summarizer role (Tier 3 per `shared/hpom.md`), and compression
  rules.
- `MAP_System/templates/CONTEXT_PACKET_TEMPLATE.md` is the packet template.
- Does not replace `notes/context-routing-guide.md`'s situational routing
  table — governs the packet that guide produces.
- Cross-linked to the Research System (DEC-015, packets carry Research
  Summaries not raw sourcing), Self-Repair System (DEC-016, stale context
  is a repair target), and Emergence (recurring context gaps become
  insights).

## DEC-018: Adopt the MAP Decision / Authority System

Status: approved
Owner: command-center (directed via hcom #19306/#19718; built by claude-lab-valo, TASK-108)
Date: 2026-07-03
Applies-To: who may decide what; Class: AUTHORITY

`MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md` identified the Decision /
Authority System as gap #4: `shared/decisions.md` records decisions well
but does not formally define who is entitled to make them, what requires
command-center approval, or how proposals get promoted to binding
decisions.

Effect:

- `MAP_System/DECISION_AUTHORITY_SYSTEM.md` applies `shared/hpom.md`'s
  authority tiers specifically to decision rights, defines human-approval
  requirements, supersession rules, and proposal-to-decision promotion.
- `MAP_System/DECISION_CLASSES.md` defines five decision classes
  (ARCHITECTURE, OWNERSHIP, SCOPE, AUTHORITY, POLICY) with the minimum
  approval level each requires.
- Cross-linked to Self-Repair (STRUCTURAL repairs are proposals routed
  through this system) and Research (unresolved contradictions are
  proposals routed through this system).
- This decision is itself class AUTHORITY and required command-center
  direction to adopt, consistent with the rule it establishes.

## DEC-019: Adopt the MAP Human Interface System

Status: approved
Owner: command-center (directed via hcom #19306/#19718; built by claude-lab-valo, TASK-110)
Date: 2026-07-03
Applies-To: operator dashboard content contract; Class: ARCHITECTURE

`MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md` identified the Human Interface
System as gap #5: a CommandCenterUI prototype exists but there was no
formal definition of what an operator dashboard should surface without
requiring a full-repository read.

Effect:

- `MAP_System/HUMAN_INTERFACE_SYSTEM.md` defines the dashboard content
  contract: current status, pending decisions, blocked tasks, review
  queue, open repairs, open research questions, recent insights, agent
  availability, and next recommended actions, plus what counts as noise
  to exclude.
- Does not replace or require rebuilding the existing CommandCenterUI
  prototype (`artifacts/command-center-ui/`) — specifies what "done" looks
  like for its live hcom/MAP wiring.
- Cross-linked to Decision/Authority (DEC-018, pending decisions),
  Self-Repair (DEC-016, open repairs), Research (DEC-015, open questions),
  and Emergence (recent insights).

## DEC-020: Adopt the MAP Risk System

Status: approved
Owner: command-center (directed via hcom #19306/#19718; built by claude-lab-valo, TASK-111)
Date: 2026-07-03
Applies-To: risk classes, register, escalation, acceptance; Class: ARCHITECTURE

`MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md` identified Risk as a secondary
gap: risk signals already exist (review severity, security second-pass,
current-state health issues, improvement backlog, constraints) but were
scattered without a register or escalation discipline.

Effect:

- `MAP_System/RISK_SYSTEM.md` defines risk classes (SECURITY, DATA,
  PROCESS, AVAILABILITY, KNOWLEDGE), reuses Self-Repair's four-level
  severity vocabulary, and defines register format, owners, review
  cadence, escalation, and acceptance.
- `MAP_System/templates/RISK_REGISTER_TEMPLATE.md` is the entry template.
- Risk acceptance is itself a decision routed through
  `DECISION_AUTHORITY_SYSTEM.md`, not a separate authority path.
- Cross-linked to Self-Repair (risk-bearing drift), Decision/Authority
  (acceptance routing), Human Interface (dashboard surfacing), and
  Research (unresolved contradictions as KNOWLEDGE-class risk).

## DEC-021: Adopt the MAP Security / Permissions System

Status: approved
Owner: command-center (directed via hcom #19306/#19718; built by claude-lab-valo, TASK-112)
Date: 2026-07-03
Applies-To: agent permission levels, destructive actions, trust boundaries; Class: AUTHORITY

`MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md` identified Security/Permissions
as a secondary gap: `AGENTS.md`'s Security Second Pass rule exists but
there was no formal permission-level model, destructive-action policy, or
trust boundary model underneath it.

Effect:

- `MAP_System/SECURITY_PERMISSIONS_SYSTEM.md` defines the trust boundary
  model (repo/machine/network), secret handling, and external-service
  policy; extends rather than replaces `AGENTS.md`'s Security Second Pass
  rule.
- `MAP_System/AGENT_PERMISSION_LEVELS.md` maps `shared/hpom.md` tiers to
  concrete read/write/shell/network permissions.
- `MAP_System/DESTRUCTIVE_ACTION_POLICY.md` defines what counts as
  destructive and the required confirmation/approval before a core agent
  acts.
- Cross-linked to Risk (SECURITY-class exposure), Decision/Authority
  (permission/scope changes require approval), and Self-Repair
  (STRUCTURAL security drift).
- This decision is itself class AUTHORITY and required command-center
  direction to adopt.

## DEC-022: Adopt the MAP Change Control System

Status: approved
Owner: command-center (directed via hcom #19306/#19718; built by claude-lab-valo, TASK-114)
Date: 2026-07-03
Applies-To: change requests, release records, rollback, changelog, retirement; Class: ARCHITECTURE

`MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md` identified Change Control as a
secondary gap: Git tooling, the git operation lock, and the release-path
smoke checklist already exist, but change request format, release-record
requirements, rollback notes, changelog policy, migration notes, version
tags, and artifact retirement were not formalized.

Effect:

- `MAP_System/CHANGE_CONTROL_SYSTEM.md` formalizes the task file itself as
  the change request, names the existing Review Gate as the diff-review
  requirement, requires the `artifacts/releases/` checklist convention
  (already used by TASK-101 through TASK-112) for any task touching
  shared/template/canonical files, and defines rollback-notes,
  changelog, migration-notes, version-tag, and retirement rules.
- Declines to add a new version-tag scheme (TASK-NNN/DEC-NNN already serve
  that role) and a new MAP-system-level changelog file (decisions.md +
  events.jsonl already serve that role) — avoids duplicating existing
  identifiers per the documentation style guide's pushback rule.
- Cross-linked to Self-Repair (rollback-as-repair), Decision/Authority
  (AUTHORITY/POLICY-class changes), Risk (irreversible-change risk), and
  Human Interface (review-queue surfacing).

## DEC-023: Adopt the MAP Project Bootstrapping System

Status: approved
Owner: command-center (directed via hcom #19306/#19718; built by claude-lab-valo, TASK-115)
Date: 2026-07-03
Applies-To: new-project bootstrap workflow; Class: ARCHITECTURE

`MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md` identified Project
Bootstrapping as a secondary gap: `notes/brain-organization-guide.md`
already defines a strong folder layout, but there was no formal workflow
requiring a new project to establish intent, assumptions, research needs,
quality standards, risks, and decision paths before its first task.

Effect:

- `MAP_System/PROJECT_BOOTSTRAPPING_SYSTEM.md` defines the six
  pre-first-task requirements and points to `RESEARCH_SYSTEM.md`,
  `RISK_SYSTEM.md`, and `DECISION_AUTHORITY_SYSTEM.md` as the source for
  three of them.
- `MAP_System/NEW_PROJECT_WIZARD.md` is the step-by-step checklist.
- Extends `notes/brain-organization-guide.md` rather than duplicating its
  folder layout; that guide now links back to this system.
- Skip conditions apply for trivial/throwaway projects per `shared/hpom.md`
  routing questions.

## DEC-024: Adopt the MAP Archive/Retention System

Status: approved
Owner: command-center (directed via hcom #19306/#19718; built by claude-lab-valo, TASK-117)
Date: 2026-07-03
Applies-To: archive statuses, retention rules, compaction cadence; Class: ARCHITECTURE

`MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md` identified Archive/Retention
as a secondary gap: `notes/brain-compaction-guide.md` already defines
compaction mechanics, but archive statuses and the distinction between
archiving and artifact retirement were not formalized.

Effect:

- `MAP_System/ARCHIVE_RETENTION_SYSTEM.md` defines archive statuses
  (ACTIVE, COMPACTED, HISTORICAL), retention rules, and draws the line
  between retirement (`CHANGE_CONTROL_SYSTEM.md`, marking an artifact
  invalid in place) and archiving (moving genuinely inactive content out
  of the active-memory budget).
- Extends `notes/brain-compaction-guide.md` rather than duplicating its
  compaction trigger/cadence logic.
- Cross-linked to Self-Repair (stale-but-active content is a repair
  target, not an archiving target), Change Control (retirement vs.
  archiving distinction), and Context System (archive/historical content
  excluded from default context).

## DEC-025: Adopt the MAP Retrospective / Learning System

Status: approved
Owner: command-center (directed via hcom #19306/#19718; built by claude-lab-valo, TASK-118)
Date: 2026-07-03
Applies-To: end-of-cycle retrospective loop; Class: ARCHITECTURE

`MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md` identified Retrospective/Learning
as the last and weakest secondary gap: the improvement backlog and
Emergence capture individual findings, but no formal end-of-cycle loop
asked what worked, what failed, what caused rework, and what should become
permanent.

Effect:

- `MAP_System/RETROSPECTIVE_SYSTEM.md` defines the retrospective loop and
  its relationship to Self-Repair's incident-scale prevention (this system
  runs at cycle scale instead).
- `MAP_System/templates/RETROSPECTIVE_TEMPLATE.md` is the record template.
- Includes RETRO-0001, a worked retrospective of the TASK-103 through
  TASK-117 gap-review build sequence itself, which found a recurring
  output_paths-registration gap for cross-linked files and applied the fix
  directly to `notes/task-authoring-guide.md` (logged in
  `shared/improvement-backlog.md` as applied).
- Cross-linked to Self-Repair, Emergence, the improvement backlog, and
  Change Control.
- This completes the full build sequence identified in
  `MAP_System/artifacts/reports/MAP-repo-systems-gap-review.md`: all systems named as
  priority or secondary gaps (Research, Self-Repair, Context,
  Decision/Authority, Human Interface, Risk, Security/Permissions, Change
  Control, Project Bootstrapping, Archive/Retention, Retrospective) are
  now built.

## DEC-026: Make Emergence Capture Mandatory Per-Project, Enforced Through MAP

Status: approved
Owner: command-center (direct operator instruction; built by claude-lab-valo, TASK-126)
Date: 2026-07-03
Applies-To: every project's bootstrap and every task's release; Class: POLICY

The operator identified that the Emergence/Insight (E/I) system was
never used during the entire ProjectUpdater build (TASK-123 through
TASK-125) despite `emergence/README.md` already existing and defining
project-level insight/idea/experiment/synthesis folders, and real
insights surfacing during that build (a Playwright install workaround, a
risk-mitigation idea, a completeness-gap pattern) that went uncaptured
until asked about directly. Operator directive: backfill proper records
for ProjectUpdater now, and make Emergence capture mandatory for every
project going forward, enforced through MAP rather than left as a
documentation-only suggestion.

Effect:

- Backfilled `INS-0011`, `INS-0012`, `INS-0013`, and `IDEA-0015` for
  ProjectUpdater (tagged `Project: ProjectUpdater`), triaged (not left
  `RAW`), and rebuilt the emergence index.
- Created `Projects/ProjectUpdater/{insights,ideas,experiments,synthesis}/`
  retroactively, matching the new bootstrap requirement below.
- `PROJECT_BOOTSTRAPPING_SYSTEM.md` (amended): added a 7th
  pre-first-task requirement ("Emergence capacity") and a new "Ongoing
  Emergence capture" section clarifying this is not a one-time bootstrap
  checkbox like the other six.
- `NEW_PROJECT_WIZARD.md` (amended): added step 7 (create empty Emergence
  folders at bootstrap) and step 9 (consider Emergence capture at every
  task's submission).
- `CHANGE_CONTROL_SYSTEM.md` (amended) and `scripts/release_task.py`
  (amended): `REQUIRED_CHECKS` now includes a literal
  `- [x] Emergence capture considered` line, mechanically blocking
  `release_task.py` from marking any task `RELEASED` without it — same
  enforcement mechanism as the three existing required checklist items.
  A checklist may honestly say "considered, nothing worth capturing";
  the gate blocks only a missing line, not a "no" answer.
- `templates/release-checklist.md` and `tests/test_release_gate.py`
  updated to match; new focused test
  `test_missing_emergence_line_blocks_release` added and passing.
- This decision is itself class POLICY and was approved directly by
  command-center instruction, per `DECISION_AUTHORITY_SYSTEM.md`.

## DEC-027: Research System Stays Specification-Only Until A Real Research Question Exists

Status: approved
Owner: claude-lab-magi (TASK-142, follow-up to TASK-129/130/140/141)
Date: 2026-07-04
Applies-To: Research System use across all projects; Class: SCOPE (core
agent, propose-and-record; not AUTHORITY or POLICY because it does not
change who may decide or a cross-MAP rule, only what is currently in bounds
for Research System use)

TASK-129/130 found the Research System (`RESEARCH_SYSTEM.md`, six templates
in `templates/research/`, `validate_research_artifacts.py`) is fully built
and validator-backed but has zero real Research Brief / Source Map / Claim
Evidence Matrix / Assumption Register / Research Summary artifacts in
`artifacts/research/` beyond the README. ProjectUpdater's bootstrap
explicitly recorded that no external-dependency research brief was needed.
The operator asked directly (TASK-142 broadcast) whether E/I and Research
need improvement and whether all built systems are actually being used.

Answer for Research, recorded as a decision rather than left implicit:

- E/I (Emergence) does not need more building — it is genuinely used and
  mechanically enforced (DEC-026, `release_task.py`'s required
  `Emergence capture considered` line). No action needed there.
- Research is different in kind: it isn't under-enforced, it's
  under-*needed*. Every task so far has had its unknowns resolved by reading
  code, existing docs, or asking the operator directly — none has hit the
  shape Research is for (an external claim, a third-party library choice, a
  contested technical fact) that benefits from a structured brief/source
  map/evidence trail. Building fake research artifacts to make the system
  look used would be the box-ticking-ceremony failure mode DEC-026 already
  named as a risk for Emergence, applied to a different system.

Effect:

- Research System stays exactly as built (validator, templates, README) with
  no forced sample artifact.
- The next task that has a genuine external/contested-fact research need
  must use `templates/research/` for it — this decision does not lower the
  bar, it only declines to invent a need that does not exist yet.
- `artifacts/research/README.md` should link this decision so a future
  reader does not mistake the empty folder for an unbuilt or abandoned
  system.
- Revisit this decision (supersede or amend) the first time a task's
  unresolved-questions or review reveals a real unverified external claim
  that should have gone through a Research Brief but didn't.

## DEC-028: MAP Commits to Software Delivery as its First Standing Proving Workflow

Status: approved
Owner: bigboss (operator), selected 2026-07-15 from gune's working-backwards
brief (`artifacts/planning/working-backwards-proving-workflow-2026-07-15.md`)
Date: 2026-07-15
Applies-To: MAP proving-workflow direction; Class: DIRECTION/SCOPE (operator
authority — this is a project-direction choice, which DECISION_AUTHORITY_SYSTEM
reserves for the operator as decision owner; reversible)

Reason: MAP is architecturally ahead on durability + mechanical gates
(INS-0022) but every recent task (197–204) was internal infrastructure, with no
real deliverable flowing through the gates (INS-0023). Applying Amazon's
working-backwards method, the operator selected **software delivery** as MAP's
first standing proving workflow: MAP designs, implements, reviews, and releases
real software, with every change gated, owned, and reversible. Software was
chosen over the research-brief and Pathwell candidates because it has the most
objective acceptance gates — the strongest fit for MAP's mechanical-gate
differentiator.

- First slice (bounded, reversible): complete **IDEA-0015's deferred import
  half** — a JSON Import button in ProjectUpdater (export shipped in TASK-136;
  import was deferred). This mitigates the registered localStorage data-loss
  risk (`Projects/ProjectUpdater/risks/RISK_REGISTER.md`) with an objective
  acceptance test (export → import round-trip restores state).
- Standing workflow: real software features flow through normal MAP
  intake → claim → implement (Codex-led) → review (Claude/core, cross-review) →
  release-gate. The research-brief candidate remains available as a second track.
- This resolves the open `shared/unresolved-questions.md` item ("first real
  workflow target: writing / software / research / PM?").
- Revisit/amend if the first feature slices show the software cadence is a poor
  fit or the operator redirects to another track.
