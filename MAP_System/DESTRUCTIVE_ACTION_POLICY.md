<!-- hpom: file: DESTRUCTIVE_ACTION_POLICY.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-112 build -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Destructive Action Policy

Companion to `SECURITY_PERMISSIONS_SYSTEM.md` and
`AGENT_PERMISSION_LEVELS.md`. Defines what counts as destructive and what
confirmation or approval it requires before a core agent (Tier 1) acts.

## What counts as destructive

An action is destructive if it is hard to reverse, affects state beyond
the agent's own in-progress work, or could discard something the operator
or another agent has not agreed to lose. This includes, non-exhaustively:

- deleting files, branches, or database tables;
- `git push --force`, `git reset --hard`, `git checkout`/`restore`/`clean`
  over uncommitted work;
- killing processes or restarting services other agents/sessions depend on;
- downgrading or removing dependencies;
- modifying CI/CD pipeline configuration;
- amending or rewriting already-pushed/shared commits;
- `--no-verify`, `--no-gpg-sign`, or other safety-check bypass flags;
- any action a reasonable reviewer would call "hard to undo."

## What is not destructive by this policy

- Normal commits, normal pushes to a branch the agent owns and no one else
  is depending on mid-work;
- creating new files, including new tasks, decisions, or repair records;
- read-only commands, including shell commands that only inspect state;
- reworking/reclaiming/resubmitting a task through the normal MAP gates
  (`map_task.py rework`, `claim_task`, `submit_task`) — these are reversible
  by design.

## Required confirmation before a destructive action

A Tier 1 core agent must not perform a destructive action without one of:

1. Explicit operator instruction covering that specific action in this
   session (a prior approval does not carry forward to a new, different
   destructive action);
2. A command-center-approved decision (`DEC-NNN`) that explicitly
   authorizes the class of action, per `DECISION_AUTHORITY_SYSTEM.md`;
3. For actions the agent itself judges necessary but not yet approved:
   stop, name the concrete risk, propose the safer alternative, and ask
   via hcom `--intent request` before acting — same standard as
   `AGENTS.md`'s general safety guidance.

## Safer-alternative-first rule

Before taking a destructive action to clear an obstacle, prefer a
reversible one: stash instead of discard, rename/move instead of delete,
supersede instead of overwrite a decision, rework instead of hard-reset a
task. This mirrors the root operating instructions and is restated here so
it is discoverable from the Security/Permissions System directly.

## Relationship to other systems

- A destructive action taken without required confirmation is a
  `STRUCTURAL`-severity, `PROCESS`-class risk per `RISK_SYSTEM.md` and
  should be logged as such if it happens.
- Authorizing a new class of destructive action (e.g., "core agents may
  force-push to X under Y condition") is itself an `AUTHORITY`-class
  decision per `DECISION_CLASSES.md`, requiring command-center approval.

## Related files

- `SECURITY_PERMISSIONS_SYSTEM.md` [[SECURITY_PERMISSIONS_SYSTEM]] — the trust-boundary model this policy
  operates within
- `AGENT_PERMISSION_LEVELS.md` [[AGENT_PERMISSION_LEVELS]] — permission levels this policy narrows for
  destructive cases
- `RISK_SYSTEM.md` [[RISK_SYSTEM]] — where an unconfirmed destructive action is logged if
  it occurs
- `DECISION_AUTHORITY_SYSTEM.md` [[DECISION_AUTHORITY_SYSTEM]] — where new destructive-action authority
  is approved
