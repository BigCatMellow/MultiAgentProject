# MAP 6.13 Assumption Red-Team (TASK-157, Wave 9)

Status: draft-active
Owner: command-center
Built by: TASK-157

## Purpose

This audit challenges the design assumptions behind the MAP 6.13 plan, not
only numeric parameters. It uses the 6.13 gap register plus bounded helper
input from `task150review-beni`, who was not the TASK-157 owner.

Helper input:

- `MAP_System/inbox/helpers/task157-assumption-red-team-beni.md`

## Findings

### RT-001: Single Entry Point May Become An Accounting Label

Assumption: operator intent will flow through the intake/decomposer contract.

Challenge: real work still arrives through direct hcom messages, helper
requests, group messages, and interrupts. If direct requests are only
repackaged after the fact, trace, budget, tiering, policy, and approval
metadata can be incomplete at the moment dispatch happens.

Route: task backlog

Follow-up: add direct-message capture or exception handling so hcom work
becomes a dispatch packet before assignment, or is explicitly marked outside
normal automation.

### RT-002: Decomposer Correctness Is More Than Field Completeness

Assumption: a decomposer output with required fields is valid enough for
downstream validators.

Challenge: a well-formed decomposition can still split work incorrectly, omit
dependencies, understate output paths, serialize independent work, or define
acceptance criteria that pass while missing user intent.

Route: Self-Repair

Follow-up: define decomposer defect classes and repair triggers for bad splits,
hidden dependencies, bad ownership boundaries, and insufficient acceptance
criteria found during review.

### RT-003: Semantic Validators Can Reproduce MAP's Blind Spots

Assumption: semantic/protocol validators create an independent verification
layer.

Challenge: if the semantic validator is built from the same assumptions and
evaluated only by MAP's own success criteria, it can shift self-confirmation
into a new component. The hard problem is not only false positives; it is
consistent false negatives on defects MAP authors also miss.

Route: Research

Follow-up: create an intentionally adversarial evaluation set for semantic
validator calibration, including examples that satisfy surface schema while
violating task intent.

### RT-004: Durable State Can Encode The Wrong Reality

Assumption: durable files and SQLite records should dominate chat memory.

Challenge: durable state is safer only when current, scoped, and canonical.
Stale status files, helper notes, snapshots, or mirrors can look more
authoritative than ephemeral hcom facts while being wrong.

Route: Self-Repair

Follow-up: add freshness/provenance checks for dispatch-driving surfaces:
agent identity, task status, helper notes, snapshots, and event-derived traces.

### RT-005: Multi-Project Isolation Is Behavioral, Not Only Metadata

Assumption: MAP can become multi-project-ready by labeling state as global or
project-local.

Challenge: Pathwell and root MAP share a repo, agent pool, operator attention,
and hcom fabric. A `project_id` field does not isolate budgets, task queues,
events, repair halts, helper notes, or UI state by itself.

Route: Risk

Follow-up: add or update a risk entry for multi-project contamination and
resource contention before write-capable multi-project UI controls exist.

### RT-006: Roster Tiers May Hide Task-Specific Capability

Assumption: agents can be grouped into stable reasoning/helper/local tiers.

Challenge: capability varies by task contract, available tools, current health,
approval state, and context. A local or cheap lane may be good at one markdown
cleanup task and unsafe on another that requires implicit policy judgment.

Route: Research

Follow-up: measure helper/local lane value by task subtype using review
outcomes, rework rate, and owner integration cost before changing roster size.

### RT-007: Formal Verification Can Over-Certify A Narrow Boundary

Assumption: proving allocator, task-claim, and git-lock invariants materially
reduces MAP's concurrency risk.

Challenge: a verified abstract protocol can be bypassed by wrapper scripts,
manual JSON edits, shell commands, export ordering, crash recovery, or human
approval timing. The proof helps only if every implementation mutation path
maps to a modeled transition.

Route: Self-Repair

Follow-up: pair each formal invariant with an implementation-boundary audit
that names scripts, commands, and fallbacks able to bypass the verified helper.

### RT-008: Scoped Circuit Breakers May Still Halt The Whole System

Assumption: circuit breakers can pause only an affected agent, lane, task type,
or subsystem.

Challenge: in a small workspace, some scopes are shared dependencies. Pausing
event writes, task mirrors, hcom, or a core reviewer can effectively pause the
system while appearing scoped.

Route: Risk

Follow-up: require every breaker scope to list dependent workflows and expected
degraded mode before enforcement becomes blocking.

### RT-009: Outcome Feedback Is A Dependency, Not A Later Nice-To-Have

Assumption: later outcome feedback will prevent learning loops from optimizing
only for validators.

Challenge: local-helper lanes, semantic validators, learning guards, and roster
composition can all learn from review/validator signals before real
post-release outcome feedback exists.

Route: task backlog

Follow-up: make outcome-feedback capture a prerequisite for learning-loop or
roster-change decisions that claim evidence from real success.

### RT-010: Operator Attention Is A Shared Bottleneck

Assumption: attention queues and mission-control visibility preserve human
authority without blocking safe progress.

Challenge: visibility can increase interrupt load. Validator halts, budget
warnings, helper conflicts, stale agents, governance decisions, and risk
questions can all route to one operator queue.

Route: Research

Follow-up: measure operator-interrupt volume and decision latency, then define
auto-defer or continue-without-operator policies for low-risk classes.

### RT-011: CommandCenterUI Becomes A Control Plane Once It Writes

Assumption: MAP_System can specify mission-control behavior while
CommandCenterUI remains a separate consumer.

Challenge: once UI controls can approve, reject, nudge, halt, or dispatch, the
UI is no longer passive. A mismatch between MAP policy and UI implementation
becomes a control-plane defect.

Route: task backlog

Follow-up: add a cross-repo control-plane release checklist for any UI feature
that mutates MAP state or initiates hcom actions.

### RT-012: Helper Notes Can Become Unvalidated Memory

Assumption: durable helper notes improve continuity without becoming source of
truth.

Challenge: helper notes are durable but not governed like task files, review
records, or shared state. As helper volume grows, stale notes may become a
parallel memory layer.

Route: Self-Repair

Follow-up: define helper-note lifecycle states, freshness checks, and cleanup
rules, especially for helper notes used by reviews or audits.

## Integration Decisions

Accepted into final TASK-157 artifacts:

- Beni RT-001 through RT-012 are represented above.
- TASK-152's validator-halt correction reinforces RT-004 and RT-008: halt
  state needs one source of truth, and scoped halts must not fork parallel
  control stores.

Not applied directly in this task:

- No new risk entries were added from TASK-157 because the declared output
  paths are audit artifacts, not the shared risk register.
- No backlog tasks were created because TASK-157 is an audit pass, not a task
  authoring wave.

## Highest Priority Follow-Ups

1. Build adversarial decomposer and semantic-validator fixtures.
2. Add implementation-boundary audit for formal invariants.
3. Add multi-project contamination/resource-contention risk entry.
4. Define helper-note lifecycle and freshness rules.
5. Measure operator attention load before adding more approval surfaces.
