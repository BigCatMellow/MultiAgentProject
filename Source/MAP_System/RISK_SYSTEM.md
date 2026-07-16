<!-- hpom: file: RISK_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-111 build, Guidelines/MAP_repo_systems_gap_review.md -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Risk System

Status: active
Decision: DEC-020
Owner: command-center
Built by: TASK-111

## What this is

Risk already appears throughout MAP: review severities, the security
second-pass rule, `shared/current-state.md` health issues, the
improvement backlog, and `shared/constraints.md`. This file formalizes
those signals into one register format so risk is tracked, owned, and
reviewed instead of only mentioned in passing wherever it happens to
surface.

## Core principle

```
A named risk with no owner and no review date is not being managed, only recorded.
```

## Risk classes

| Class | What it covers | Example |
|---|---|---|
| `SECURITY` | trust boundaries, injection, auth, CSRF, secrets | AGENTS.md's Security Second Pass rule |
| `DATA` | data loss, corruption, drift between recorded and true state | mirror/SQLite drift (see `SELF_REPAIR_SYSTEM.md`) |
| `PROCESS` | ownership confusion, gate bypass, silent scope change | duplicate task claims, missed no-self-review |
| `AVAILABILITY` | agent/session limits, tool outages, lock contention | session-limit exhaustion, git operation lock contention |
| `KNOWLEDGE` | acting on unverified or stale claims | unresolved contradictions per `RESEARCH_SYSTEM.md` |

## Risk severity

Reuse the same four-level shape as `SELF_REPAIR_SYSTEM.md` so agents do not
learn a second severity vocabulary:

| Severity | Meaning |
|---|---|
| `COSMETIC` | annoyance only, no real exposure |
| `DRIFT` | exposure exists but nothing is currently blocked or exploited |
| `BLOCKING` | exposure actively prevents safe progress or is actively exploitable |
| `STRUCTURAL` | exposure touches authority, security boundary, or irreversible action |

## Risk register format

Use `templates/RISK_REGISTER_TEMPLATE.md`. Each entry states: risk class,
severity, description, trigger/likelihood, blast radius, owner, review
cadence, and current acceptance status.

Risks live in a single running register per project/system rather than
one file per risk, since risks are usually revisited rather than closed
outright — `MAP_System/shared/RISK_REGISTER.md` for MAP-system-level risk,
`Projects/<PROJECT_NAME>/risks/RISK_REGISTER.md` for project-level risk.

## Risk owners

Every register entry has exactly one owner, same discipline as
`AGENTS.md` DEC-003 (one owner per active task). The owner is accountable
for keeping the entry current, not necessarily for personally fixing the
underlying issue.

## Risk review cadence

- `STRUCTURAL` and `BLOCKING` risks: reviewed every session that touches
  the affected area, and whenever a related repair or decision is made.
- `DRIFT` risks: reviewed at each `HEALTH_CHECK_REPORT` pass (see
  `SELF_REPAIR_SYSTEM.md`).
- `COSMETIC` risks: reviewed opportunistically; no fixed cadence required.

A risk with no review in longer than its cadence allows is itself a
`DRIFT`-class Self-Repair finding (stale risk tracking).

## Risk escalation

- `SECURITY` and `STRUCTURAL`-severity risks of any class escalate to
  command-center immediately via hcom `--intent request`
  (Issue/Options/Recommendation/Needed format), same as any other
  STRUCTURAL matter per `DECISION_AUTHORITY_SYSTEM.md`.
- `BLOCKING` risks that a core agent can mitigate directly (e.g., a
  mechanical fix) may be handled and logged; if mitigation requires
  judgment beyond the acting agent's confidence, escalate.
- `DRIFT`/`COSMETIC` risks do not require escalation; log and track.

## Risk acceptance

Accepting a risk (choosing not to fix it now) is a decision, not a
non-action. Use `DECISION_CLASSES.md` to classify it — accepting a
`SECURITY`/`STRUCTURAL` risk is at minimum a `SCOPE`-class decision and
often `AUTHORITY`/`POLICY`-class, requiring command-center approval per
`DECISION_AUTHORITY_SYSTEM.md`. Record the acceptance in the risk register
entry (`Status: ACCEPTED`) and, if it is command-center-approved, also as
a `DEC-NNN` entry.

## Relationship to other systems

```
Self-Repair fixes drift; Risk tracks what could go wrong if drift or exposure is not fixed.
Decision/Authority governs who may accept a risk instead of fixing it.
Human Interface surfaces open STRUCTURAL/BLOCKING risks to the operator.
Research's unresolved contradictions are KNOWLEDGE-class risk entries.
```

- **`SELF_REPAIR_SYSTEM.md`**: a repair fixes a specific instance of
  drift; a risk register entry tracks the standing exposure class that
  drift instance belongs to. A recurring `BLOCKING` repair should also get
  (or update) a Risk register entry, not just a Repair Record.
- **`DECISION_AUTHORITY_SYSTEM.md`**: risk acceptance routes through this
  system's approval tiers exactly like any other decision — Risk does not
  invent a separate acceptance authority.
- **`HUMAN_INTERFACE_SYSTEM.md`**: open `STRUCTURAL`/`BLOCKING` risk
  entries belong on the operator dashboard alongside pending decisions and
  open repairs.
- **`RESEARCH_SYSTEM.md`**: an unresolved contradiction that could not be
  settled from available sources is a `KNOWLEDGE`-class risk, not just an
  open research question — log it in both places if it is load-bearing
  for a decision.

## Related files

- `SECURITY_PERMISSIONS_SYSTEM.md` [[SECURITY_PERMISSIONS_SYSTEM]] — the trust-boundary model SECURITY-class
  risks are checked against
- `CHANGE_CONTROL_SYSTEM.md` [[CHANGE_CONTROL_SYSTEM]] — where an irreversible-change risk is
  logged as a DATA-class entry
- `PROJECT_BOOTSTRAPPING_SYSTEM.md` [[PROJECT_BOOTSTRAPPING_SYSTEM]] — where a new project's initial risk
  register draws from this system
- `templates/RISK_REGISTER_TEMPLATE.md` [[RISK_REGISTER_TEMPLATE]] — the register entry template
- `shared/RISK_REGISTER.md` [[RISK_REGISTER]] — MAP-system-level risk register (create when
  the first risk is logged)
- `SELF_REPAIR_SYSTEM.md` [[SELF_REPAIR_SYSTEM]] — where risk-bearing drift gets fixed
- `DECISION_AUTHORITY_SYSTEM.md` [[DECISION_AUTHORITY_SYSTEM]] — where risk acceptance is approved
- `HUMAN_INTERFACE_SYSTEM.md` [[HUMAN_INTERFACE_SYSTEM]] — where open risks are surfaced
- `RESEARCH_SYSTEM.md` [[RESEARCH_SYSTEM]] — where unresolved contradictions become
  KNOWLEDGE-class risk
- `shared/constraints.md` [[constraints]] — hard boundaries this system does not override
- `AGENTS.md` [[AGENTS]] — the existing Security Second Pass rule this system
  formalizes as one instance of SECURITY-class risk handling
- `Guidelines/MAP_repo_systems_gap_review.md` — the gap review that
  identified this system as a secondary gap
