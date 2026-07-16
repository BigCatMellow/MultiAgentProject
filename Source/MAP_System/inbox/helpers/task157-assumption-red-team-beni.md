# TASK-157 Assumption Red-Team Helper Note

Status: draft helper note, not final TASK-157 output
Helper: task150review-beni
Requested by: codex-lab-mozu
Date: 2026-07-13

## Scope

This note challenges MAP 6.13 design assumptions, not numeric parameters. It is
input for TASK-157's final assumption red-team artifact and should be integrated
or rejected by the TASK-157 owner.

Read:

- `MAP_System/tasks/TASK-157.json`
- `MAP_System/artifacts/planning/map-613-master-implementation-plan.md`
- `Guidelines/6.13/MAP-Gap-Register.md`
- `Guidelines/6.13/MAP-System/04-MAP-Formal-Verification.md`
- `MAP_System/artifacts/planning/map-runtime-migration-inventory.md`
- `MAP_System/artifacts/planning/map-runtime-migration-plan.md`
- `MAP_System/artifacts/planning/map-decomposer-spec.md`
- `MAP_System/artifacts/planning/map-resilience-controls-spec.md`
- `MAP_System/artifacts/planning/map-task-tiering-spec.md`
- `MAP_System/artifacts/audits/map-threat-model.md`
- `MAP_System/shared/RISK_REGISTER.md`

## Red-Team Findings

### RT-001: Single Entry Point May Become A Social Fiction

Assumption: once an intake/decomposer contract exists, operator intent will
mostly flow through it.

Challenge: hcom still supports direct agent requests, helper requests, group
messages, and interrupts. Real work is already arriving through those paths,
including this helper request. A "single entry point" can become an accounting
label applied after the fact unless there is a capture/repackaging mechanism
for direct messages. Downstream trace, budget, tiering, and policy checks then
inherit incomplete intake metadata.

Route: task backlog

Suggested follow-up: add a direct-message capture task that turns hcom requests
into dispatch packets or explicit exceptions before later waves assume all work
has `gap_score`, `risk_class`, `task_tier`, approval, and trace metadata.

### RT-002: Decomposer Correctness Is Defined By Fields, Not By Truth

Assumption: if the decomposer emits all required fields, the resulting subtasks
are valid enough for downstream validators to manage.

Challenge: the current decomposer spec requires good fields, but does not yet
define adversarial tests for wrong splits: missing dependency edges,
over-narrow output paths, acceptance criteria that pass while missing the user
intent, or tasks that serialize work unnecessarily and hide parallelism. A
well-formed decomposition can still be semantically wrong, and downstream
checks may treat it as authoritative.

Route: Self-Repair

Suggested follow-up: create decomposer defect classes and repair triggers for
bad splits, missing ownership boundaries, hidden dependencies, and acceptance
criteria that reviewers later find insufficient.

### RT-003: Validators May Shift Trust, Not Remove It

Assumption: adding protocol and semantic validators creates an independent
verification layer.

Challenge: the semantic validator is itself a judgment system. If it is built
from the same project assumptions and reviewed only through MAP's own success
criteria, it can move self-confirmation into a new component. The risk is not
only false positives; it is a validator that consistently misses defects that
MAP's authors also miss.

Route: Research

Suggested follow-up: require an external or intentionally independent
evaluation set for semantic validator calibration, including examples that
violate MAP's preferred framing while satisfying surface schemas.

### RT-004: Durable State Can Still Encode The Wrong Reality

Assumption: durable files and SQLite records are safer than chat memory and
therefore should dominate.

Challenge: durable state is only better if it is current, scoped, and
canonical. TASK-148 found three agent identity surfaces and no complete
reconciliation path. A stale `status.json`, stale helper note, or legacy
task mirror can be more persuasive than an ephemeral hcom fact precisely
because it looks canonical. "Durable wins" needs freshness and provenance,
not just path priority.

Route: Self-Repair

Suggested follow-up: add freshness/provenance checks for state surfaces that
drive dispatch: agent identity, task status, helper notes, state snapshots,
and event-derived traces.

### RT-005: Project Isolation Is Treated As A Metadata Problem

Assumption: MAP can become multi-project-ready by deciding which fields are
global versus project-local.

Challenge: Pathwell shares the same repo, `map.db`, task graph, event log, and
agent pool. A later `project_id` field may not be enough if failure domains,
budgets, risk registers, operator attention, helper notes, and command-center
UI state remain shared operationally. Isolation is behavioral, not only
schema-level.

Route: Risk

Suggested follow-up: register a multi-project contamination/resource-contention
risk if TASK-157 confirms no hard isolation boundary exists for task queues,
events, budgets, and repair halts.

### RT-006: Roster Tiers Assume Stable Capability Classes

Assumption: agents can be reliably grouped into reasoning, cheap-language, and
local/mechanical tiers, or into a simpler two-tier alternative.

Challenge: capability varies by task context, prompt, available tools,
approval state, and current session health. A cheap-language or local helper
may be good at one "markdown cleanup" and bad at another that requires
implicit policy judgment. Static lanes can hide the true variable: confidence
under a specific task contract.

Route: Research

Suggested follow-up: measure helper value by lane and task subtype using real
review outcomes, rework rate, and owner integration cost before adding or
removing tiers.

### RT-007: Formal Verification May Over-Certify The Wrong Boundary

Assumption: proving allocator, task-claim, and git-lock invariants materially
reduces MAP's highest concurrency risk.

Challenge: TLA+ or state-machine tests can prove the abstract protocol while
the actual failure occurs in translation boundaries: wrapper scripts, shell
commands, manual JSON edits, export-to-file ordering, crash recovery, or human
approval timing. The formal artifact could create confidence in a small core
while the unsafe path remains outside the modeled transition system.

Route: Self-Repair

Suggested follow-up: pair each formal invariant with an implementation-boundary
audit naming the scripts, manual operations, and fallbacks that can bypass the
verified protocol.

### RT-008: Circuit Breakers Can Preserve Safety By Destroying Throughput

Assumption: scoped circuit breakers pause only the affected agent, lane, task
type, or subsystem.

Challenge: the scopes may not be independent in a small multi-agent workspace.
Pausing event writes, task mirrors, hcom, or a core reviewer can effectively
pause everything while appearing "scoped." The design needs a dependency map
of breaker scopes; otherwise a local halt can become a system halt without the
operator realizing it.

Route: Risk

Suggested follow-up: add a breaker-blast-radius risk or backlog item requiring
each breaker scope to list dependent workflows and expected degraded mode.

### RT-009: Outcome Feedback Is Planned But Not Yet Available

Assumption: later outcome feedback will prevent MAP from optimizing only for
validators.

Challenge: several waves depend conceptually on outcome evidence, but the
outcome feedback spec is still future work. Until it exists, local-helper
lanes, semantic validators, learning guards, and roster choices may all learn
from review artifacts and validator pass/fail instead of real post-release
outcomes.

Route: task backlog

Suggested follow-up: make outcome-feedback capture a prerequisite for any
learning loop or roster-change decision that claims evidence from "worked in
reality."

### RT-010: Operator Attention Is Treated As Routable Capacity

Assumption: attention queues, approval gates, and mission-control visibility
let the operator remain the final authority without becoming the bottleneck.

Challenge: visibility can increase interrupt load. If every validator halt,
budget warning, helper conflict, stale agent, and governance decision routes to
one attention queue, the operator becomes the shared dependency for progress.
The design distinguishes actionable from routine items, but not yet the
operator's sustainable decision budget or absentee behavior for low-risk work.

Route: Research

Suggested follow-up: measure operator-interrupt volume and decision latency
before and after mission-control/protocol-validator rollout, then set explicit
auto-defer or continue-without-operator policies for low-risk classes.

### RT-011: CommandCenterUI Is Treated As A Consumer, But Control Loops Need Release Coupling

Assumption: MAP_System can specify mission-control and command-center behavior
while the live CommandCenterUI repo remains a separate consumer.

Challenge: once UI buttons can approve, reject, nudge, halt, or dispatch, the
UI is no longer a passive consumer. A mismatch between MAP_System policy and
the external app implementation becomes a control-plane defect. The current
"separate follow-up task" rule is good, but TASK-157 should challenge whether
read-only-to-write-capable UI transitions need a joint release gate across
both repos.

Route: task backlog

Suggested follow-up: add a cross-repo control-plane release checklist for any
CommandCenterUI feature that can mutate MAP state or initiate hcom actions.

### RT-012: Helper Notes May Become A Parallel Memory System

Assumption: durable helper notes improve continuity without becoming source of
truth.

Challenge: helper notes are intentionally durable, but they are not governed
like task files, reviews, or shared state. They can contain stale findings,
partial reads, or abandoned recommendations. As helper volume grows, these
notes may function as an unvalidated memory layer that future agents read as
evidence.

Route: Self-Repair

Suggested follow-up: define helper-note lifecycle states and stale-note cleanup
or summarization rules, especially for notes that inform reviews or audits.

## Cross-Cutting Questions For TASK-157 Owner

- Which assumptions require a formal risk entry now, versus a backlog task?
- Which findings should be tested by adversarial fixtures rather than prose
  policy?
- Which existing waves should gain a do-not-proceed gate because their
  assumptions are still unverified?
- Which assumptions can be accepted explicitly as command-center decisions
  rather than treated as defects?
