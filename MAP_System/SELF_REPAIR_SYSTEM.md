<!-- hpom: file: SELF_REPAIR_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-105 build, Guidelines/MAP_repo_systems_gap_review.md -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Self-Repair System

Status: active
Decision: DEC-016
Owner: command-center
Built by: TASK-105

## What this is

MAP already repairs itself in pieces: validators, reconciliation scripts,
stale reports, and health checks all exist and run. This file formalizes
what they already do into one module: severity levels, repair records,
health check reports, automatic-repair permission boundaries, escalation
rules, verification plans, and follow-up prevention.

## Core principle

```
MAP can repair structure automatically.
MAP can propose repairs to authority.
MAP cannot silently rewrite its own authority.
```

A repair fixes drift between recorded state and true state. It does not
invent new intent, change ownership, or override a decision.

## Repair severity levels

| Severity | Meaning | Example | Who may act |
|---|---|---|---|
| `COSMETIC` | Formatting, stale metadata date, non-blocking note | HPOM `last_verified` date behind current work | Any agent, no record required beyond a normal commit |
| `DRIFT` | Recorded state disagrees with true state but nothing is blocked | task JSON mirror behind SQLite, agent status stale | Any core agent, auto-repair allowed, log a `REPAIR_RECORD` |
| `BLOCKING` | Drift prevents a gate, task, or agent from proceeding correctly | expired lease not reclaimed, task graph validation failing | Core agent, auto-repair allowed if the fix is mechanical (re-export, re-run reconciler); propose first if the fix requires judgment |
| `STRUCTURAL` | Repair would change ownership, authority, decisions, or approved output | task output_paths were wrong and approval already happened, a decision needs superseding | Propose only — requires command-center or normal decision process, same as any other decision |

Rule: severity is about blast radius and reversibility, not about how the
issue was found. A `STRUCTURAL` repair discovered by an automated validator
still requires proposal, not silent action.

## Health check reports

A Health Check Report is a snapshot of what the existing validators found,
read together instead of one at a time. It answers: is MAP internally
consistent right now?

Sources a Health Check Report should pull from:

- `scripts/validate_shared_state.py` — HPOM metadata completeness on shared files
- `scripts/validate_decisions.py` — decision log integrity, superseded chains
- `scripts/validate_task_graph.py` — task graph consistency
- `scripts/validate_events.py` — event log shape, legacy aliases
- `scripts/reconcile_agents.py` — agent status vs hcom/session reality
- `scripts/map_emergence.py stale` — stale/placeholder/dangling emergence records
- `scripts/map_metrics.py` — task-flow health (cycle time, rework rate, gate pass rate)
- `scripts/local_assistant_health.py` — local/Ollama helper availability
- `tests/test_exporter_invariants.py` — SQLite/file-mirror agreement

Use `templates/repairs/HEALTH_CHECK_REPORT_TEMPLATE.md` to record one pass.
A report is a read-only snapshot; it does not itself repair anything.

## Repair records

Every `DRIFT`, `BLOCKING`, or `STRUCTURAL` repair gets a Repair Record using
`templates/repairs/REPAIR_RECORD_TEMPLATE.md`, filed under
`MAP_System/repairs/`. `COSMETIC` repairs do not need a record.

A Repair Record states: what was found, which validator/check surfaced it,
severity, what was changed, what was verified after the change, and whether
this is a one-off or should become a validator/template/decision (see
Follow-Up Prevention below).

## Automatic-repair permissions (HPOM tiers applied to repair)

Applying `shared/hpom.md` authority tiers:

- **Tier 1 (core agents)** may perform `DRIFT` and mechanical `BLOCKING`
  repairs directly (e.g., re-run `migration/export_to_files.py` to resync
  mirrors, as done in TASK-103's review cycle) and must file a Repair
  Record.
- **Tier 1** may *propose* a `STRUCTURAL` repair but may not apply it
  without command-center approval or a normal decision entry.
- **Tier 2 (visible helpers)** may run read-only health checks and draft a
  Health Check Report; they do not apply repairs.
- **Tier 3 (local assistants)** may draft a Health Check Report summary or
  classify a finding's severity for a core agent to confirm; they do not
  decide severity or apply repairs.
- **Tier 0 (command-center/human)** resolves all `STRUCTURAL` repairs and
  any repair a core agent is not confident classifying. See
  `DECISION_AUTHORITY_SYSTEM.md` for how a STRUCTURAL repair's proposed
  fix is routed to approval as a decision.

## Escalation rules

- A `BLOCKING` repair that requires judgment (not mechanical) escalates to
  a Repair Record with an explicit proposed fix, posted via hcom
  `--intent request`, before the agent acts.
- A `STRUCTURAL` repair always escalates — draft the Repair Record with a
  proposed fix and stop; do not apply until approved.
- If a repair reveals the same class of drift for the third time (see
  Follow-Up Prevention), escalate as a Repair Record proposing a
  validator or template change, not just another one-off fix.

## Verification plans

Every Repair Record states how the fix was verified, not just that it was
applied. Minimum bar:

- Re-run the specific validator(s) that surfaced the issue.
- Re-run `scripts/validate_task_graph.py` and
  `tests/test_exporter_invariants.py` if the repair touched task/mirror
  state.
- Re-run the full suite (`scripts/run_tests.sh`) if the repair touched
  more than one subsystem.

A repair without a stated verification step is incomplete, same standard
as a task without acceptance criteria.

## Follow-up prevention

If a repair is the first occurrence, log the Repair Record and move on.

If a repair is a repeat of a known class of drift:

1. Check `shared/improvement-backlog.md` for an existing entry; add one if
   missing.
2. Propose the fix become permanent: a validator addition, a template
   change (e.g., a required field that would have caught it), or a
   decision (e.g., a stricter default in `map_task.py create`).
3. Do not just keep filing the same repair repeatedly — a third
   recurrence without a prevention proposal is itself a process gap worth
   raising to command-center.

`RETROSPECTIVE_SYSTEM.md` runs the same discipline at a larger cadence;
Self-Repair handles it in-line, per-incident.

## Relationship to other systems

```
Research verifies facts before they become project truth.
Self-Repair detects when facts, state, or mirrors have drifted or gone stale.
Emergence turns a recurring repair into a durable insight or idea.
HPOM governs who may act on a repair, and at what authority tier.
Memory/decisions absorb the corrected state once repaired.
Context (`CONTEXT_SYSTEM.md`, DEC-017) treats stale/conflicting context as a DRIFT-class repair target.
```

- **Research System**: a stale or contradictory claim caught by research
  (see `RESEARCH_SYSTEM.md` date-sensitivity and contradiction rules) is a
  `DRIFT` or `BLOCKING` repair target here, not a separate mechanism. If a
  Research Summary reveals project truth has drifted, file a Repair
  Record referencing the summary.
- **Emergence System**: a repair that recurs, or a repair whose fix
  generalizes beyond the single incident, should be captured as an
  `INS-NNNN` insight (see `emergence/README.md`) so it can be promoted
  into a validator or decision instead of being repeated silently.
- **HPOM**: repair authority is not a separate ladder — it is
  `shared/hpom.md`'s existing tiers applied to a specific task shape
  (repair instead of build/review).

## Folder structure

```
MAP_System/
  SELF_REPAIR_SYSTEM.md      ← this file
  repairs/
    README.md                 ← process + quick-start
    <REPAIR-NNNN>-<slug>.md   ← individual repair records
    <HEALTH-NNNN>-<slug>.md   ← individual health check reports
  templates/repairs/
    REPAIR_RECORD_TEMPLATE.md
    HEALTH_CHECK_REPORT_TEMPLATE.md
```

Project-level repairs (when a project needs isolated repair history) live
under `Projects/<PROJECT_NAME>/repairs/` and `Projects/<PROJECT_NAME>/health/`
following the same shape.

## Agent rule

```
Fix what is mechanical.
Propose what is structural.
Record every DRIFT-or-higher repair.
Prevent the next occurrence, not just this one.
```

## Related files

- `HUMAN_INTERFACE_SYSTEM.md` [[HUMAN_INTERFACE_SYSTEM]] — where open (non-terminal) repair records
  are surfaced to the operator
- `CONTEXT_SYSTEM.md` [[CONTEXT_SYSTEM]] — where stale or conflicting context is treated as
  a DRIFT-class repair target
- `DECISION_AUTHORITY_SYSTEM.md` [[DECISION_AUTHORITY_SYSTEM]] — where a STRUCTURAL repair's proposed
  fix is routed to approval as a decision
- `RISK_SYSTEM.md` [[RISK_SYSTEM]] — where recurring/standing exposure from a repair
  class is tracked as a risk register entry
- `SECURITY_PERMISSIONS_SYSTEM.md` [[SECURITY_PERMISSIONS_SYSTEM]] — where STRUCTURAL security drift
  (secrets, over-broad permissions, unreviewed network-facing changes) is
  defined
- `CHANGE_CONTROL_SYSTEM.md` [[CHANGE_CONTROL_SYSTEM]] — where rollback-as-repair is documented for
  a bad change
- `ARCHIVE_RETENTION_SYSTEM.md` [[ARCHIVE_RETENTION_SYSTEM]] — where stale-but-active content is
  distinguished from a genuine archiving candidate
- `RETROSPECTIVE_SYSTEM.md` [[RETROSPECTIVE_SYSTEM]] — this system's incident-scale follow-up
  prevention, viewed across a whole cycle
- `repairs/README.md` [[repairs/README]] — folder layout and quick-start
- `templates/repairs/` — the two repair templates
- `RESEARCH_SYSTEM.md` [[RESEARCH_SYSTEM]] — where stale/contradictory facts are first
  identified as claims, before they become repair targets
- `emergence/README.md` [[emergence/README]] — where recurring repairs become durable insights
- `shared/hpom.md` [[hpom]] — the authority tiers applied to repair actions
- `shared/decisions.md` [[decisions]] — where structural repairs land once approved
- `shared/improvement-backlog.md` [[improvement-backlog]] — where recurring repair classes are
  tracked until a permanent fix lands
- `Guidelines/MAP_repo_systems_gap_review.md` — the gap review that
  identified this system as priority #2
