<!-- hpom: file: DECISION_AUTHORITY_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-108 build, Guidelines/MAP_repo_systems_gap_review.md -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Decision / Authority System

Status: active
Decision: DEC-018
Owner: command-center
Built by: TASK-108

## What this is

`shared/decisions.md` already records decisions well: what was decided,
who owns it, and what it superseded. This file formalizes the layer above
that log — who is allowed to make a given decision in the first place,
what must escalate to command-center, and how a recommendation becomes
binding. See `DECISION_CLASSES.md` for the class table this system
routes against.

## Core principle

```
Agents may recommend decisions.
Only the proper authority may make them binding.
```

Recording a decision in `shared/decisions.md` is not the same as having
had the authority to make it. This system exists so that gap does not
appear silently — every decision entry should be traceable to the
authority tier that was actually entitled to approve it.

## Authority tiers, applied to decisions

This reuses `shared/hpom.md`'s existing tiers; it does not invent a new
ladder. It answers the decision-specific question at each tier.

| Tier | Worker | Decision rights |
|---|---|---|
| 0 | command-center / human | Final authority on any decision class. Required for AUTHORITY and POLICY classes (see `DECISION_CLASSES.md`), and for any SCOPE decision that changes what agents are allowed to do unsupervised. |
| 1 | core agents (Codex, Claude) | May decide and record ARCHITECTURE and OWNERSHIP class decisions within an already-approved scope, without per-decision sign-off, as long as the decision does not touch AUTHORITY or POLICY class territory. May propose AUTHORITY/POLICY decisions but not finalize them. |
| 2 | visible temporary helpers | May recommend a decision in any class; may not record one in `shared/decisions.md` directly. Their recommendation becomes a core agent's proposal. |
| 3 | local assistants / Ollama | May draft a decision recommendation (e.g., "the evidence points to X") for a core agent to evaluate. May never record, approve, or imply a decision is final. |
| 4 | Aider with local model | No decision rights. Executes named-file edits after a decision is already made. |

## Human-approval requirements

A decision requires explicit command-center approval before it is recorded
as `approved` (not just `proposed`) when it:

- changes agent authority, permission boundaries, or who may act
  unilaterally (AUTHORITY class);
- changes MAP-wide policy that governs all projects, not just one task
  (POLICY class);
- reverses or narrows a prior command-center-approved decision;
- is the resolution of a `STRUCTURAL` repair per `SELF_REPAIR_SYSTEM.md`;
- is the resolution of a research contradiction that Research System
  contradiction-handling could not settle (see `RESEARCH_SYSTEM.md`).

Everything else (ARCHITECTURE, OWNERSHIP, most SCOPE decisions inside an
already-approved project) may be decided and recorded by a core agent,
provided it does not conflict with `shared/constraints.md` or an existing
decision.

## Supersession rules

- A decision is never silently deleted. To change it, add a new `DEC-NNN`
  entry and mark the old one `Status: superseded` with
  `superseded_by: DEC-NNN` (matching the existing pattern already used for
  DEC-007 and DEC-012 in `shared/decisions.md`).
- Only the tier that could have approved the original decision may
  approve its supersession. A core agent may supersede its own
  ARCHITECTURE/OWNERSHIP decision; only command-center may supersede an
  AUTHORITY/POLICY decision, even if a core agent proposes the change.
- `scripts/validate_decisions.py` already checks this structurally
  (`superseded_by` fields, active/superseded counts); this system defines
  the judgment call the validator cannot make — whether the *right party*
  approved the change, not just whether the fields are well-formed.

## Proposal-to-decision promotion

Mirrors the Emergence promotion pattern deliberately, so agents do not
need to learn two different escalation shapes:

```
Observation / Recommendation
  → Proposed decision (drafted by a core agent, or lifted from a helper/
     local-model recommendation)
  → Authority check (which tier may finalize, per the table above)
  → Recorded in shared/decisions.md as approved, or returned for rework
```

A proposed decision that needs command-center approval should be posted
via hcom `--intent request` in the Issue/Options/Recommendation/Needed
format (per the operator's standing instruction), not silently recorded as
`approved` and hoped past review.

## Relationship to other systems

```
HPOM defines the general authority tiers.
Decision/Authority applies those tiers specifically to what becomes binding.
Self-Repair's STRUCTURAL repairs are proposals that must pass through here.
Research's unresolved contradictions are proposals that must pass through here.
Emergence's promoted ideas become decisions or tasks through here.
```

- **`shared/hpom.md`**: source of the tier definitions this system routes
  against; this file does not redefine tiers, only their decision rights.
- **`SELF_REPAIR_SYSTEM.md`**: a `STRUCTURAL` repair is, by definition, a
  decision — it routes through this system's human-approval requirement
  rather than being self-approved by whichever agent found the drift.
- **`RESEARCH_SYSTEM.md`**: a Research Summary that changes project truth
  becomes a `DEC-NNN` entry; if the summary logged an unresolved
  contradiction, that decision needs command-center approval per the rule
  above, not a core agent's best guess.
- **`emergence/README.md`**: a promoted idea becomes a decision or task
  through the same authority check — Emergence's "promote deliberately"
  rule and this system's approval requirement are the same discipline
  applied at different stages.

## Related files

- `HUMAN_INTERFACE_SYSTEM.md` [[HUMAN_INTERFACE_SYSTEM]] — where pending decisions requiring
  command-center approval are surfaced to the operator
- `RISK_SYSTEM.md` [[RISK_SYSTEM]] — where risk acceptance routes through this system's
  approval tiers
- `SECURITY_PERMISSIONS_SYSTEM.md` [[SECURITY_PERMISSIONS_SYSTEM]] — where permission/scope changes route
  through this system's approval tiers
- `CHANGE_CONTROL_SYSTEM.md` [[CHANGE_CONTROL_SYSTEM]] — where AUTHORITY/POLICY-class changes route
  through this system before release
- `PROJECT_BOOTSTRAPPING_SYSTEM.md` [[PROJECT_BOOTSTRAPPING_SYSTEM]] — where a new project's decision-paths
  step draws from this system
- `DECISION_CLASSES.md` [[DECISION_CLASSES]] — the decision class table this system routes
  against
- `shared/hpom.md` [[hpom]] — the tier definitions this system applies to decisions
- `shared/decisions.md` [[decisions]] — the decision log itself
- `SELF_REPAIR_SYSTEM.md` [[SELF_REPAIR_SYSTEM]] — where STRUCTURAL repairs become proposals
  routed through this system
- `RESEARCH_SYSTEM.md` [[RESEARCH_SYSTEM]] — where research conclusions become proposals
  routed through this system
- `emergence/IDEA_PROMOTION_RULES.md` [[IDEA_PROMOTION_RULES]] — the parallel promotion discipline
  for ideas
- `Guidelines/MAP_repo_systems_gap_review.md` — the gap review that
  identified this system as priority #4
