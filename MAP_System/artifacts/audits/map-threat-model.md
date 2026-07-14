# MAP Threat Model (TASK-156, Wave 8)

Status: draft-active
Owner: command-center
Built by: TASK-156

## Purpose

This threat model identifies the control surfaces where MAP can accidentally
over-authorize agents, corrupt durable state, leak sensitive information, or
let one bad action cascade. It focuses on pre-dispatch governance and the
surfaces named by TASK-156.

## Assets

| Asset | Why it matters |
|---|---|
| `map.db` and task mirrors | canonical task state, claims, dependencies, approvals |
| `events/events.jsonl` | durable audit trail and route/review evidence |
| `shared/` systems files | current rules, decisions, risks, and state |
| output artifacts | reviewed work products consumed by later tasks |
| hcom messages/transcripts | coordination, approvals, task requests |
| local machine/process state | shell commands can affect other sessions/repos/services |
| credentials/secrets | must not enter durable MAP files or external services |
| CommandCenterUI controls | operator-facing control plane for future dispatch/intervention |

## Actors

| Actor | Trust level |
|---|---|
| command-center/human | Tier 0 final authority |
| core agents | Tier 1, broad but policy-bound execution |
| visible helpers | Tier 2, bounded review/draft support |
| local assistants/Ollama | Tier 3, draft-only and no shell/network by default |
| Aider local wrapper | Tier 4, named-file edit lane under wrapper constraints |
| external MCP/connectors | trusted only for scoped tool action, not MAP authority |
| compromised or confused agent/tool | untrusted; must be contained by policy and validators |

## Control Surfaces

### Repo

Threats:

- task edits outside declared `output_paths`;
- hidden modification of shared policy/decision files;
- unreviewed broad rewrites across unrelated systems;
- output path collisions between active tasks.

Controls:

- task output path ownership;
- `validate_task_graph.py` collision checks;
- pre-dispatch output scope check;
- review gate and no-self-review checks;
- risk register entries for recurring process exposure.

### Shell

Threats:

- destructive commands discard work or alter shared state;
- process kills/restarts interrupt other agents;
- dependency changes downgrade safety or break validators;
- safety-check bypass flags hide real failures.

Controls:

- `DESTRUCTIVE_ACTION_POLICY.md`;
- shell actions classified before assignment;
- Tier 1 `require_approval` for destructive operations;
- helpers/local assistants rejected for destructive shell work;
- command execution logs and validator reruns after state changes.

### Filesystem

Threats:

- writes outside `/home/home/Projects/MultiAgentProject` or approved roots;
- secrets written into durable MAP files;
- generated artifacts overwrite another task's work;
- stale mirrors read as current truth.

Controls:

- workspace roots and sandboxing;
- secret-handling rules in `SECURITY_PERMISSIONS_SYSTEM.md`;
- file mirror validation;
- canonical store degradation policy;
- task output path collision checks.

### Local Helpers

Threats:

- local assistant output treated as final;
- malformed output enters canonical state;
- local helper is assigned shell/network/destructive work;
- local model hallucination becomes unverified project truth.

Controls:

- Tier 3 draft-only permission;
- capability whitelist tests;
- semantic/protocol validators;
- core-agent integration ownership;
- Research/Risk handling for load-bearing claims.

### Compression And Memory Proxies

Threats:

- compressed summaries omit blockers, approvals, or ownership boundaries;
- stale context is treated as current state;
- memory proxy invents intent not present in durable files;
- handoff loses validator failures or review findings.

Controls:

- durable files as source of truth;
- startup reads of AGENTS/status/snapshots/handoffs;
- context drift treated as Self-Repair `DRIFT`;
- checkpoint/handoff artifacts for long work;
- pre-dispatch reads from canonical task state rather than chat memory.

### MCP And Connectors

Threats:

- connector writes outside task scope;
- external service receives sensitive MAP content;
- plugin/tool authority is confused with MAP decision authority;
- network integration is added without approval.

Controls:

- connector use scoped to explicit task need;
- external-service policy;
- no secrets in durable files or uploaded content;
- new integrations route through decision authority;
- pre-dispatch network/trust-boundary checks.

### hcom

Threats:

- routine progress messages become noisy and hide real requests;
- request/approval messages use ambiguous format;
- helper spawned headless, hiding approval prompts;
- an agent treats another helper's recommendation as binding;
- wrong recipient or group causes scope leakage.

Controls:

- `--intent request` only for decisions, approvals, blockers, conflicts, or
  risk questions;
- Issue/Options/Recommendation/Needed format for operator requests;
- visible helper tabs with `--terminal wezterm-tab`;
- helpers may recommend but not approve;
- durable artifacts record final state, not chat alone.

### CommandCenterUI

Threats:

- UI action mutates canonical state without the same CLI policy checks;
- stale UI state dispatches already-claimed or blocked work;
- intervention controls bypass kill switch, policy checker, or review gates;
- UI displays wrong repo path or stale health status.

Controls:

- UI must call sanctioned commands/helpers, not write canonical state directly;
- read-only view first for liveness and mission control;
- policy checker and kill-switch state read before dispatch/intervention;
- canonical repo path validation and repair records for path drift;
- disabled/dry-run intervention controls until backend checks exist.

## Abuse Cases

| Abuse case | Expected control |
|---|---|
| Helper assigned final approval review | pre-dispatch `reject`; capability whitelist test |
| Local assistant assigned shell command | pre-dispatch `reject`; Tier 3 no shell |
| Core agent assigned force reset without approval | `require_approval` before assignment |
| New connector integration added as ordinary implementation | `require_approval` via network/authority gate |
| Stale compressed handoff says task is done | canonical task/event state wins |
| CommandCenterUI dispatches blocked task | backend policy checker rejects |
| Poisoned output consumed by downstream task | dependency/quarantine containment blocks downstream |

## Residual Risks

- Policy currently exists mostly as prose; automated pre-dispatch enforcement
  is still future work.
- Text-derived risk/destructive classification can miss subtle cases until
  task packets carry structured metadata.
- CommandCenterUI intervention paths will need a separate implementation
  review once controls become write-capable.
- Connectors and MCP tools may need per-tool allowlists once MAP starts using
  them for writes rather than read-only context.

These residual risks are tracked in `MAP_System/shared/RISK_REGISTER.md`.
