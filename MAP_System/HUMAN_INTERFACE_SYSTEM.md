<!-- hpom: file: HUMAN_INTERFACE_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-110 build, Guidelines/MAP_repo_systems_gap_review.md -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Human Interface System

Status: active
Decision: DEC-019
Owner: command-center
Built by: TASK-110

## What this is

MAP already produces everything an operator needs to know — it is spread
across `shared/current-state.md`, `workflow/task_graph.json`,
`shared/decisions.md`, emergence records, repair records, and research
artifacts. This file defines what a dashboard surface should assemble from
those sources so the operator does not have to read the whole repository
to know what needs their attention.

## Core principle

```
The human should see decisions, risks, and next actions — not raw system noise.
```

This system defines what to surface, not a specific UI implementation. A
CommandCenterUI prototype already exists
(`artifacts/command-center-ui/standalone-ui-map-db-repair-2026-07-02.md`);
this file specifies the content contract that prototype (or any future
dashboard) should satisfy, without requiring a rebuild.

## Dashboard surface

A conforming dashboard shows, at minimum:

| Section | Source | Refresh trigger |
|---|---|---|
| Current status | `shared/current-state.md` | On file change |
| Pending decisions | `shared/decisions.md` proposals awaiting command-center approval per `DECISION_AUTHORITY_SYSTEM.md` | On new AUTHORITY/POLICY-class proposal |
| Blocked tasks | `graph/runner.py` `blocked_tasks` | On runner run |
| Review queue | `graph/runner.py` `submitted_tasks` | On runner run |
| Open repairs | `MAP_System/repairs/*.md` with `Status: PROPOSED` per `SELF_REPAIR_SYSTEM.md` | On new repair record |
| Open risks | `shared/RISK_REGISTER.md` entries with `Status: OPEN` at `BLOCKING`/`STRUCTURAL` severity per `RISK_SYSTEM.md` | On new/updated risk entry |
| Open research questions | `MAP_System/artifacts/research/` briefs/summaries with unresolved contradictions or open assumptions, per `RESEARCH_SYSTEM.md` | On new/updated research artifact |
| Recent insights | `emergence/INDEX.md` recent `RAW`/`CANDIDATE` entries | On `map_emergence.py` capture |
| Agent availability | `agents/status.json` / `graph/runner.py` `available_agents` | On status change |
| Next recommended actions | `graph/runner.py` `recommended_action` / `next_route` | On runner run |

## Assembly rule

A dashboard is a read-only aggregation. It does not:

- decide anything itself (decisions still route through
  `DECISION_AUTHORITY_SYSTEM.md`);
- apply repairs (repairs still route through `SELF_REPAIR_SYSTEM.md`);
- replace the durable files it reads from — it is a view, not a second
  source of truth.

If the dashboard's view disagrees with the files it reads from, the files
win, and the disagreement is itself a `DRIFT`-severity finding per
`SELF_REPAIR_SYSTEM.md`.

## What counts as noise (do not surface by default)

- Full `events/events.jsonl` history — surface only the most recent
  `N` entries or a filtered view (e.g., last 24h, or by task).
- Routine `ACK`/`inform`-intent hcom traffic — the dashboard is not a chat
  log; link to `hcom transcript`/`hcom events` for that.
- `RELEASED`/`DONE`/terminal tasks beyond a short recent-completions list.
- Historical `artifacts/` and `archive/` content, per the same
  forbidden-context rule in `CONTEXT_SYSTEM.md`.

## Relationship to other systems

```
Decision/Authority surfaces what needs command-center approval.
Self-Repair surfaces open repairs and health status.
Research surfaces open questions and unresolved contradictions.
Emergence surfaces recent insights worth the operator's attention.
HPOM/Orchestration surfaces agent availability and the next recommended action.
```

- **`DECISION_AUTHORITY_SYSTEM.md`**: the dashboard's "pending decisions"
  section is exactly the set of proposals awaiting the approval levels
  that system defines — it does not introduce a separate approval
  concept.
- **`SELF_REPAIR_SYSTEM.md`**: "open repairs" is the set of Repair Records
  not yet `APPLIED`/`APPROVED`/`REJECTED`; a `STRUCTURAL` repair proposal
  should be prominent here since it needs command-center action.
- **`RESEARCH_SYSTEM.md`**: "open research questions" surfaces Research
  Briefs without a final Research Summary, and Research Summaries whose
  Assumption Register still has `OPEN` entries.
- **`emergence/README.md`**: "recent insights" is a filtered slice of
  `emergence/INDEX.md`, not the full artifact set — enough for the
  operator to notice a pattern without reading every record.
- **`shared/hpom.md` / `graph/runner.py`**: agent availability and
  recommended next action come directly from the existing runner output;
  this system does not duplicate that logic, only specifies that it
  belongs on the dashboard.

## Relationship to CommandCenterUI

`artifacts/command-center-ui/standalone-ui-map-db-repair-2026-07-02.md`
documents prior CommandCenterUI/map.db repair work. This system does not
replace that prototype or require a rewrite — it specifies the content
contract (the table above) that any dashboard implementation, including a
future iteration of CommandCenterUI, should satisfy. Wiring live
hcom/MAP state into a UI remains open per
`shared/current-state.md`'s Known Health Issues; this file defines what
"done" looks like for that wiring, not the wiring itself.

## Related files

- `artifacts/command-center-ui/` — existing prototype and repair notes
- `DECISION_AUTHORITY_SYSTEM.md` [[DECISION_AUTHORITY_SYSTEM]] — source of the pending-decisions section
- `SELF_REPAIR_SYSTEM.md` [[SELF_REPAIR_SYSTEM]] — source of the open-repairs section
- `RESEARCH_SYSTEM.md` [[RESEARCH_SYSTEM]] — source of the open-research-questions section
- `RISK_SYSTEM.md` [[RISK_SYSTEM]] — source of the open STRUCTURAL/BLOCKING risk section
- `emergence/README.md` [[emergence/README]] — source of the recent-insights section
- `shared/hpom.md` [[hpom]] — source of agent-availability and next-action logic
- `CHANGE_CONTROL_SYSTEM.md` [[CHANGE_CONTROL_SYSTEM]] — where the review-queue's diff-review
  requirement is defined
- `CONTEXT_SYSTEM.md` [[CONTEXT_SYSTEM]] — source of the forbidden-context rule this
  dashboard's noise exclusions follow
- `graph/README.md` [[graph/README]] — the runner output the dashboard's status/queue
  sections read from
- `Guidelines/MAP_repo_systems_gap_review.md` — the gap review that
  identified this system as priority #5
