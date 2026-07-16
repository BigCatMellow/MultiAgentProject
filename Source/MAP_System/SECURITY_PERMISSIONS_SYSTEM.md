<!-- hpom: file: SECURITY_PERMISSIONS_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-112 build, Guidelines/MAP_repo_systems_gap_review.md -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Security / Permissions System

Status: active
Decision: DEC-021
Owner: command-center
Built by: TASK-112

## What this is

`AGENTS.md` already requires a security-framed second review pass for any
task whose outputs add a network-facing or write-capable component. This
file formalizes what that pass checks against: agent permission levels,
read/write/delete boundaries, shell and network policy, secret handling,
external-service policy, and the trust boundary model. It extends the
existing rule; it does not replace it.

## Core principle

```
Agents should have the least permission needed to complete the task.
```

## Trust boundary model

MAP has three trust boundaries an agent action can cross:

| Boundary | Crossed when | Governs |
|---|---|---|
| Repo boundary | writing outside the current task's `output_paths`, or outside `/home/home/Projects/MultiAgentProject` | file write scope |
| Machine boundary | running a shell command that affects processes, other repos, or system state beyond this repo | shell/process scope |
| Network boundary | making an outbound network call, exposing a listener, or handling external-service credentials | network/secret scope |

Crossing any of these is not automatically forbidden — it is a signal to
check the permission level and, for the machine/network boundaries, to
run the Security Second Pass (`AGENTS.md`) if the change is network-facing
or write-capable.

## See also: permission levels and destructive-action policy

The concrete permission-level table and the destructive-action policy are
kept as separate companion files so each stays short and scannable:

- `AGENT_PERMISSION_LEVELS.md` — what each HPOM tier may read/write/execute
- `DESTRUCTIVE_ACTION_POLICY.md` — what counts as destructive and what
  confirmation or approval it requires

## Secret handling

- Never write secrets (API keys, tokens, credentials, `.env` contents)
  into `shared/`, `tasks/`, `events/events.jsonl`, `handoffs/`, or any
  other durable MAP file. These are durable and widely read.
- If a task's output legitimately needs a secret at runtime, name the
  environment variable or secret-manager reference in the file, never the
  value.
- If an agent encounters a secret already committed to the repo, treat it
  as a `SECURITY`-class, `STRUCTURAL`-severity risk per `RISK_SYSTEM.md`
  and escalate immediately — do not silently continue past it or log the
  secret value anywhere while reporting it.

## External service policy

- Calling an external service (web fetch, API call, third-party tool) is
  in bounds for research, verification, or an explicitly task-scoped
  integration.
- Uploading MAP content to an external service (pastebin, diagram
  renderer, third-party gist) is a network-boundary crossing that should
  be treated as at least mildly sensitive — do not upload anything that
  could contain secrets, unresolved security findings, or content the
  operator has not indicated is fine to share externally.
- New external-service integrations (not just calls) are a
  `SECURITY`-class risk and an `ARCHITECTURE`- or `AUTHORITY`-class
  decision depending on scope — route through `DECISION_AUTHORITY_SYSTEM.md`.

## Relationship to other systems

```
Risk tracks SECURITY-class exposure as a standing register entry.
Decision/Authority governs who may approve a permission or scope change.
Self-Repair handles STRUCTURAL security drift as a repair, escalated per this system.
HPOM's existing tiers are the base this system's permission levels extend.
```

- **`AGENTS.md`**: the Security Second Pass rule remains the operative
  gate for network-facing/write-capable task outputs; this system is the
  reference material that pass checks against, not a replacement for it.
- **`RISK_SYSTEM.md`**: every trust-boundary crossing that is not clearly
  safe is at minimum a candidate `SECURITY`-class risk register entry.
- **`DECISION_AUTHORITY_SYSTEM.md`**: changing an agent's permission level,
  or approving a new external-service integration, is an `AUTHORITY`- or
  `POLICY`-class decision requiring command-center approval.
- **`SELF_REPAIR_SYSTEM.md`**: a discovered secret, an over-broad
  permission, or an unreviewed network-facing change is a `STRUCTURAL`
  repair — propose, do not silently fix.

## Related files

- `AGENT_PERMISSION_LEVELS.md` [[AGENT_PERMISSION_LEVELS]] — permission levels mapped to HPOM tiers
- `DESTRUCTIVE_ACTION_POLICY.md` [[DESTRUCTIVE_ACTION_POLICY]] — destructive-action definitions and
  required confirmation/approval
- `AGENTS.md` [[AGENTS]] — the existing Security Second Pass rule this extends
- `RISK_SYSTEM.md` [[RISK_SYSTEM]] — where SECURITY-class exposure is tracked
- `SELF_REPAIR_SYSTEM.md` [[SELF_REPAIR_SYSTEM]] — where a discovered secret, over-broad
  permission, or unreviewed network-facing change is a STRUCTURAL repair
- `DECISION_AUTHORITY_SYSTEM.md` [[DECISION_AUTHORITY_SYSTEM]] — where permission/scope changes are approved
- `shared/hpom.md` [[hpom]] — the base authority tiers this system's permission
  levels map onto
- `Guidelines/MAP_repo_systems_gap_review.md` — the gap review that
  identified this system as a secondary gap
