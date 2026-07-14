# MAP Degradation Policy (TASK-155, Wave 7)

Status: draft-active
Owner: command-center
Built by: TASK-155

## Purpose

Degradation policy defines what MAP may still do when a dependency is missing,
unhealthy, or untrusted. The default is to preserve canonical state and keep
safe, bounded work moving when evidence supports it.

This is a policy design artifact. It does not change current enforcement.

## Default Rule

Fail closed for canonical writes. Fail open only for read-only inspection,
drafting, or unrelated work whose inputs and outputs do not touch the degraded
dependency.

## Degradation Matrix

| Dependency | Degraded condition | Default behavior | Allowed work | Blocked work |
|---|---|---|---|---|
| Validator | validator unavailable, crashing, or producing malformed result | fail closed for writes it protects | read-only inspection; draft repair record; rerun validator | task approval/release; task graph mutation; event schema change |
| Cloud tier | paid/cloud model unavailable or over budget | continue local-eligible work only | local summaries, repo scans, mechanical checks, review of existing artifacts | paid dispatch; broad decomposition needing cloud reasoning |
| Canonical store | SQLite, event log, or mirror state unavailable/untrusted | block writes; allow safe reads from snapshot | inspect backups/snapshots; draft health report; operator request | claim/submit/approve/export; new task creation |
| Local model | Ollama/local helper unavailable or malformed | route to core or skip helper lane | core agent work; read-only health check | local-only required tasks; autonomous local helper dispatch |
| Operator absent | no response to gated request | hold gated actions; continue ungated work | non-gated tasks, review, repair drafts, validation | authority decisions, structural repair apply, budget override, global halt clear |

## Validator Degradation

Validators protect state boundaries and therefore fail closed for the boundary
they validate.

Examples:

- If `validate_task_graph.py` cannot run, do not approve task graph changes.
- If `validate_events.py` fails unexpectedly, do not add new event schema
  behavior until the failure is classified.
- If mirror validation fails after export, stop normal dispatch that depends
  on those mirrors and file a repair/dead-letter record as appropriate.

Fail-open exception: a core agent may continue read-only diagnosis and produce
draft artifacts that are clearly not approved state.

## Cloud Tier Degradation

Cloud degradation includes provider outage, network failure, spend-rate halt,
or policy disallowing paid dispatch.

Behavior:

- runner suppresses paid/cloud helper recommendations;
- agent loops do not spawn cloud helpers for optional work;
- local/no-cost lanes continue only when task tier and risk allow them;
- work that needs cloud reasoning waits or is reassigned to a core agent if
  the core agent can safely complete it without extra paid dispatch.

Do not treat unknown cost as zero. Unknown paid cost is degraded cost data and
routes through the cost governance and kill-switch specs.

## Canonical Store Degradation

The canonical store is the state authority: `map.db`, events, and derived task
mirrors. If it is unavailable or untrusted, MAP must stop mutating it.

Allowed:

- read-only inspection of snapshots, backups, events, and existing files;
- health check report;
- repair record proposal;
- operator request with Issue/Options/Recommendation/Needed.

Blocked:

- task claims, submissions, approvals, releases;
- task creation or dependency graph edits;
- export/reconcile writes unless the repair is a mechanical, validated
  restoration under SELF_REPAIR_SYSTEM rules.

If SQLite and file mirrors disagree, SQLite remains preferred only when it is
readable and validators indicate mirrors are stale rather than the DB being
corrupt.

## Local Model Degradation

Local helper degradation should not block core work unless the task explicitly
depends on a local lane.

Behavior:

- mark local lane unavailable in runner-visible state;
- skip helper proposals that require local model output;
- route draft/summary work to core or visible helper only if bounded;
- record malformed output as circuit-breaker input if repeated.

Local models may never be the sole authority for repair severity, approval,
task completion, or canonical mutation.

## Operator Absent

Operator absence is not permission to infer approval.

Hold:

- command-center approval gates;
- structural repair application;
- budget limit increases and global halt clears;
- destructive actions, privacy/scope-risk decisions, and policy changes.

Continue:

- already-approved implementation work;
- read-only validation and review;
- draft repair records or risk notes;
- unrelated ungated tasks.

If a blocked gated item prevents all progress, declare standby or route to
wait/reconcile. Do not spam repeated hcom requests.

## Fail-Open And Fail-Closed Vocabulary

| Term | Meaning |
|---|---|
| `fail_closed` | Stop writes or dispatch for the affected boundary until evidence clears it. |
| `fail_open_readonly` | Allow diagnosis, reading, and draft artifacts only. |
| `fail_open_local` | Allow local/no-cost work whose task tier and inputs are safe. |
| `fail_open_unrelated` | Continue tasks that do not depend on the degraded component. |

Every degradation decision should record scope. A validator outage for events
does not automatically stop unrelated markdown drafting; a canonical store
halt does stop task claims and approvals globally.

## Recovery

Recovery requires objective evidence:

- validators rerun successfully;
- canonical store and mirrors reconcile;
- cost/halt state is clear or operator-approved;
- local model health check passes;
- operator approval arrives for gated work;
- dead-letter or repair records are closed or scoped away from normal work.

Clear events should state what was degraded, what evidence cleared it, and
which lanes are back in service.
