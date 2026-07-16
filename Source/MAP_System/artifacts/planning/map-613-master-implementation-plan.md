# MAP 6.13 Master Implementation Plan

- Status: draft, pending corroboration from `claude-lab-zera` helper lanes
- Owner: `codex-lab-mozu`
- Thread: `map-613-improvement-plan`
- Source corpus: `Guidelines/6.13/MAP-System/00-MAP-Index.md` through `11-MAP-Lessons-Learned.md`
- Corroboration read so far: `MAP-Gap-Register.md`, `MAP-Extension-Plan.md`,
  `MAP-Repo-Review-List.md`, `MAP-The-Synthesized-System.md`,
  simulation result summaries, `MAP-Validator-Specification.md`, and
  `MAP-Tool-Evaluation-Appendix.md`
- Partial peer corroboration: `claude-lab-zera` hcom #27129 identified missing
  cold-start/migration, multi-project, roster-composition, and semantic
  validator work items.
- Helper corroboration: `map613-peripheral-docs-naga` hcom #27168 identified
  missing liveness/heartbeat, durable execution, assumption red-team,
  mission-control TUI, and concrete simulation-test-drive probes.
- Helper corroboration: `map613-sim-prototypes-lumo` hcom #27184 identified
  sensitivity/robustness grading as the one simulation-derived practice still
  missing from the plan.
- Corroboration lane: `claude-lab-zera` covering remaining duplicate/prototype
  review with visible helper agents once approval clears
- Created: 2026-07-13

## Executive Summary

The 6.13 notes are not mainly asking for more MAP doctrine. Most doctrine from
the 6.13 roadmap has already been built in TASK-103 through TASK-126:
Research, Self-Repair, Context, Decision/Authority, Human Interface, Risk,
Security/Permissions, Change Control, Project Bootstrapping,
Archive/Retention, Retrospective, and enforced Emergence capture.

The next improvement wave should make MAP more mechanical at runtime:

1. Make operator intent enter through a single routable intake surface.
2. Add trace IDs and causal event structure so work can be reconstructed from
   shared state.
3. Specify the decomposer: how raw intent becomes correct subtasks, dependency
   edges, output paths, acceptance criteria, and routing metadata.
4. Add a cold-start/migration plan before shipping new runtime layers.
5. Add liveness heartbeats, a reaper, and operator mission-control visibility.
6. Add cost governance and an operator kill switch before any more autonomy.
7. Add protocol/compliance validation and the harder semantic output validator
   with eager halt on real defects, but measured false-positive control.
8. Add task classification, gap scoring, and fixed local-helper lanes before
   dispatch.
9. Add outcome feedback so "worked in reality" outranks "passed validation."
10. Add dead-letter, idempotency, circuit-breaker, durable resume, recovery, and degradation
   behavior for failed work.
11. Enforce capability and destructive-action gates before dispatch.
12. Add a measured Library/knowledge layer only if summaries, wikilinks, and
   staleness tracking all land together.
13. Add multi-project and roster-composition assessments.
14. Add narrow formal verification for the task allocator, claim lock, and git
   operation lock design.
15. Add repeatable sensitivity/robustness grading so real measurements are
   classified as structurally robust vs. economically parameter-sensitive before
   they drive production decisions.

The plan below turns the 6.13 spine into implementable MAP tasks. It deliberately
avoids one broad "improve MAP" task because that would hide ownership,
acceptance criteria, review routing, and rollback boundaries.

## Source Synthesis

### Core Principles From 00-02

- Coordinate through directly-readable shared state, not relayed status chains.
- Gate irreversible or collective actions behind thresholds with redundant
  safeguards.
- Build in dependency order: correct state, single entry point, visibility,
  enforcement, routing and emergence, resilience, governance.
- Minimum viable MAP is: correct shared state, single entry point, and an
  independent verification layer.

### Detailed Requirements From 03

- Score MAP against a multi-agent failure taxonomy, not only past incidents.
- Emit structured action records with actor, action, target, timestamp, and
  causal parent.
- Track task-level traces across HPOM, hcom, emergence, and task files.
- Add idempotency keys to write operations.
- Add a dead-letter queue and explicit retry/replay policy.
- Add circuit breakers for repeatedly failing agents or subsystems.
- Add Jidoka-style halt authority: detect, stop, fix, root-cause.
- Add a separate verification layer for protocol compliance; do not rely on
  self-report.
- Add task tiers and local-model lanes so local helpers own bounded support
  categories instead of competing with cloud agents.
- Add pre-dispatch gates for high-risk actions and capability whitelisting.

### Corrections From Synthesized And Simulation Docs

- Threshold-gated validator halting was cut by simulation. The corrected rule is
  eager halt on first real validator signal, paired with strong false-positive
  measurement and accuracy work.
- Strict routing and universal peer review were cut as net-negative once the
  validator already catches defects.
- Emergence should auto-add routine, high-confidence capabilities and only
  surface genuinely uncertain requirements.
- Local/helper utilization is a routing-rule problem, not a spawn-count problem.
- The real black boxes are the validator and the decomposer. Both need explicit
  design and measurement before MAP depends on them.
- "Validator" means two different things and must be split:
  hcom/MATOCP/protocol compliance is mostly structural; semantic output
  correctness is the harder Layer 2 judge problem with the ~1% false-positive
  target.
- Deterministic Layer 1 checks improve catch rate and reduce cost, but do not
  lower fuzzy Layer 2 false positives. The ~1% false-positive target must be
  solved as a judge-accuracy/calibration problem, not assumed to emerge from
  more schema/tests/invariants.
- Cost governance and outcome feedback are architectural additions, not optional
  polish: one caps spend, the other prevents MAP from optimizing only for its
  own validators.
- The Library/knowledge layer pays only as a full design: compact summaries,
  wikilinks to detail, and event-driven staleness tracking. Summaries alone are
  worse than no library.
- Heartbeats and durable/resumable execution are distributed-systems hygiene:
  silent agents need reaping, and long tasks need checkpoint/resume instead of
  restart-from-zero.
- Operator observability needs a mission-control surface, not just an inbox:
  vitals, roster with heartbeat dots, flight board, attention queue, event
  stream, drill-down, and intervention keybindings.

### Formal Verification From 04

- Use TLA+ only for the highest-risk concurrency invariants.
- Target specs: task ID uniqueness, mutual exclusion for git operation lock,
  orphan-lock freedom, and deadlock freedom for the small abstract design.
- Keep the scope to 2-3 abstract agents and design proof, then pair it with
  runtime tests because a verified spec does not prove the Python matches it.

### Organization And Emergence From 05-06

- Treat allocator, locks, validators, and status surfaces as platform services.
- Treat emergence as an enabling subsystem, not a final authority.
- Give stream-aligned agents a clear what/why and autonomy over how.
- Add subsystem APIs so agents consume platform capabilities as services.
- Make gap detection explicit before execution:
  - scalar gap score;
  - capability pass;
  - coverage pass;
  - suggestions for missing requirements.
- Add inward improvement carefully:
  - stable evaluator first;
  - multi-critic review for high-gap cases;
  - end-of-cycle memory only after enough trajectory data exists.

### Cautions From 07-11

- Written rules cannot enforce themselves; validators are not optional.
- Central routing must stay narrow and mechanical to avoid becoming a fragile
  bottleneck.
- CRDT-style convergence is not correctness; correctness validators remain
  required.
- Anomaly validators need false-positive telemetry from day one.
- Infrastructure can backfire; measure before and after each new layer.
- Eager halts can lose trust if false positives are high; fix validator
  accuracy rather than dulling the halt trigger.
- Do not cite metaphors as proof. When adopting external claims, route real
  disputed facts through the Research System.
- Measure real repo parameters before trusting simulated economics: shipped
  defect vs. false-halt cost, local-vs-cloud defect rate, file churn, compression
  ratio, latency, and operator approval load.
- Treat cold-start/migration as an implementation risk in its own right. The
  current project has already lived through repo drift and two-copy
  reconciliation, so migration cannot be hidden inside later feature tasks.

## Current MAP Baseline

### Already Built Or Mostly Built

- Canonical repo decision: `shared/canonical-repo.md`, DEC-014.
- SQLite task claims: `db/claims.py`, DEC-009.
- Atomic task auto-ID allocation: `scripts/map_task.py create --task-id auto`.
- Git operation lock: `scripts/git_operation_lock.py`.
- Task mirror reconciliation: `scripts/validate_task_mirrors.py`.
- Event validation with historical warning baseline: `scripts/validate_events.py`.
- Agent status and limit watcher: `agents/status.json`,
  `scripts/limit_watcher.py`.
- Local helper policy and runner: `notes/local-model-helper-guide.md`,
  `scripts/local_runner.py`.
- Aider wrapper policy: `scripts/aider_wrapper.py`.
- Approval, review, release, decision, shared-state, risk, context, repair,
  research, and emergence validators.
- CommandCenterUI content contract: `HUMAN_INTERFACE_SYSTEM.md`.

### Partly Built But Not Yet Runtime-Enforced Enough

- Operator intake exists as `scripts/intake_request.py`, but direct operator to
  agent messages still happen and are not mechanically repackaged into a single
  dispatch path.
- Events are structured enough for validation, but not yet a full causal trace
  with required `trace_id` and `parent_event_id`.
- MATOCP is documented in `Guidelines/llm-communication-rules.md`, but there is
  no independent hcom/protocol validator with telemetry.
- Local helper policy exists, but tasks are not automatically tiered into local
  lanes before core-agent dispatch.
- Approval gates exist in the runner, but capability/destructive-action checks
  are not a unified pre-dispatch policy checker.
- Self-Repair exists, but validator halt/root-cause loops are not unified into
  one dispatch-blocking system state.

### Missing Or Not Evident

- TLA+ or equivalent formal spec artifacts for allocator/lock invariants.
- Explicit decomposer specification and tests.
- Cold-start/migration plan for moving from current MAP state to the next
  runtime architecture without another repo-drift or state-mirror incident.
- Cost governance: token/cost accounting, budgets, spend-rate circuit breaker,
  and kill switch.
- Semantic output-correctness validator specification, measurement harness, and
  false-positive adjudication process. This is separate from the hcom/MATOCP
  protocol validator.
- Heartbeat/liveness detection and reaper for hung agents.
- Durable/resumable execution for multi-step work using checkpoints, event
  replay, and idempotency keys.
- Outcome feedback events and validator blind-spot rate.
- Dead-letter queue for failed dispatches or failed agent-loop task attempts.
- Idempotency registry for MAP write operations.
- Circuit-breaker logic that temporarily stops routing to failing agents or
  subsystems.
- Committed poisoned-state recovery plan: detect, roll back, reconcile, and
  record root cause after bad state reaches canonical state.
- Degradation policy: fail-open/fail-closed choices for cloud, validator,
  canonical store, local model, and absent operator.
- Threat model for filesystem, shell, repo, compression proxy, local helpers,
  MCP/connectors, and agent permissions.
- Library/knowledge layer with staleness tracking, if real compression/churn
  measurements justify it.
- Research pass over external repo candidates before Library/tool adoption:
  `iurykrieger/claude-bedrock`, `ccf/agentcairn`,
  `Roshan02-CIT/Knowledge-graph-driver-rag-for-agentic-coding-tools`,
  `WenyuChiou/agent-collab-skills`, and `milisp/codexia`.
- Multi-project reality assessment: how reusable MAP state behaves when
  Pathwell and other projects share agents, queues, decisions, risks, and
  resource limits.
- Roster composition assessment: whether the proposed reasoning /
  cheap-language / local-mechanical split should be three tiers or two tiers,
  and how many agents belong in each tier.
- Mission-control TUI design and prototype plan: vitals bar, roster panel,
  flight board, attention queue, event stream, trace drill-down, and
  intervention keybindings. This extends `HUMAN_INTERFACE_SYSTEM.md`; it is not
  covered by intake/dispatch work.
- Explicit assumption red-team step to challenge the design assumptions, not
  only calibrate parameter values.
- Repeatable sensitivity/robustness grading methodology from Round 6:
  classify each load-bearing conclusion by how much of plausible parameter
  space it survives, then label it `robust`, `conditional`, or `unsupported`
  before using it to steer validator, Library, routing, or learning decisions.
- MAST-style failure taxonomy coverage map and regression test matrix.
- Subsystem API index that says how agents consume allocator, lock, validators,
  emergence, local helpers, and status surfaces as services.

## Implementation Wave

### Wave 0: Convert This Plan Into MAP Tasks

- Goal: preserve ownership and review boundaries.
- Output: TASK-147+ records, one task per work package below.
- Acceptance:
  - each task has explicit `output_paths`;
  - each task has binary acceptance criteria;
  - each task names verification commands;
  - no task claims "implement everything."

### Wave 1: Single Entry And Subsystem APIs

Candidate tasks:

1. Build command-center intake routing contract.
   - Output: `MAP_System/ORCHESTRATION_ENTRYPOINT_SYSTEM.md` or a focused
     update to existing command-center notes; `scripts/intake_request.py`
     acceptance tests.
   - Behavior: raw operator request becomes a structured dispatch packet with
     task type, scope, risk, gap score placeholder, output paths, and required
     approval decision.

2. Specify the decomposer.
   - Output: `MAP_System/artifacts/planning/map-decomposer-spec.md` and tests
     around `scripts/intake_request.py` or successor code.
   - Behavior: intent becomes subtasks with dependency edges, output paths,
     acceptance criteria, risk class, required approvals, routing lane, and
     rollback expectation.

3. Add subsystem API index.
   - Output: `MAP_System/shared/subsystem-apis.md`.
   - Contents: allocator API, git lock API, task claim API, event API,
     validator API, emergence API, local-helper API, status API.

4. Add direct-message exception handling.
   - Behavior: when an agent receives a direct broad operator instruction, it
     records a dispatch packet or asks the orchestrator to repackage it instead
     of silently treating chat as the canonical task.

### Wave 1.5: Cold Start And Migration

Candidate tasks:

1. Write current-state migration inventory.
   - Output: `MAP_System/artifacts/planning/map-runtime-migration-inventory.md`.
   - Covers repo/canonical state, SQLite/file mirrors, task graph, event log,
     hcom session state, helper notes, agent status, Pathwell/private project
     state, and CommandCenterUI assumptions.

2. Write migration rollout plan.
   - Output: `MAP_System/artifacts/planning/map-runtime-migration-plan.md`.
   - Includes order of operations, freeze/lock points, rollback points,
     validation commands, operator checkpoints, and "do not proceed if" gates.

3. Add migration smoke checks.
   - Verify canonical repo path, task mirrors, event baseline, agent status,
     and CommandCenterUI state before and after each runtime-layer change.

### Wave 2: Traceable Visibility

Candidate tasks:

1. Define event trace schema.
   - Add required or next-generation fields: `trace_id`, `parent_event_id`,
     `actor`, `action`, `target`, `task_id`, `thread`.
   - Preserve legacy compatibility through the existing warning baseline.

2. Add event append helper.
   - Provide one script/API for appending structured events so agents stop hand
     writing inconsistent JSONL.

3. Add trace reconstruction command.
   - Given `task_id` or `trace_id`, print the causal chain across events,
     handoffs, review artifacts, and hcom thread references.

4. Add real-parameter measurement.
   - Measure shipped-defect vs. false-halt cost, local-vs-cloud defect rate,
     file churn, compression ratio, wall-clock latency, hcom volume, and
     operator approval load.
   - Output: calibration report used to tune later validators and library work.

5. Add sensitivity/robustness grading.
   - Output: `MAP_System/artifacts/audits/map-sensitivity-robustness-method.md`
     plus a first grading report.
   - After each real-parameter measurement, grade which conclusions hold across
     plausible ranges and which are parameter-sensitive.
   - Expected labels: `robust`, `conditional`, `unsupported`.
   - Initial candidates: eager halt vs. threshold, idempotency value, Library
     payoff, pruning-guard value, and local-helper routing economics.

6. Add simulation-test-drive acceptance probes.
   - Probe 1: measure whether coordination happened through shared state or
     point-to-point hcom relay for selected tasks.
   - Probe 2: prove a validator can actually halt dispatch, not only log.
   - Use these as acceptance tests for the relevant Wave 1/Wave 4 tasks.

### Wave 2.5: Liveness And Mission Control

Candidate tasks:

1. Add heartbeat/liveness surface.
   - Agents write `last_seen`, active task, lane, and state to shared status.
   - The status surface distinguishes alive, idle, working, blocked, suspect,
     and broken.

2. Add reaper behavior.
   - Stale heartbeat reclaims or dead-letters the task.
   - Repeated stale heartbeats feed the circuit breaker.
   - Operator-visible event records explain each reaping action.

3. Specify mission-control TUI.
   - Output: `MAP_System/artifacts/planning/mission-control-tui-spec.md`.
   - Panels: vitals bar, roster with heartbeat dots, task flight board,
     attention queue, filterable event stream.
   - Drill-down: task trace tree, agent lane/history, cost, halt reason.
   - Interventions: approve/deny gate, kill runaway task, resume agent, bump
     budget, override false halt.
   - Candidate stack: Python Textual, k9s-style interaction model.

4. Prototype read-only mission-control view.
   - Read from existing durable MAP state first.
   - Do not create a second source of truth.
   - Defer intervention keybindings until read-only state is correct.

### Wave 3: Cost Governance And Kill Switch

Candidate tasks:

1. Add event cost fields.
   - Fields: `tokens_in`, `tokens_out`, `model_tier`, `estimated_cost`.
   - Preserve legacy event compatibility.

2. Add dispatch budget checks.
   - Per-task and per-day budget counters block or request approval before
     additional paid work.

3. Add spend-rate circuit breaker and kill switch.
   - A guarded halt flag stops dispatch on runaway spend.
   - Operator can clear it only through the normal authority path.

### Wave 4: Validator Architecture And Halt Authority

Candidate tasks:

1. Add MATOCP/hcom protocol validator.
   - Validate routine hcom messages for required intent, token form where
     applicable, and request-format requirements for operator decisions.
   - Report false-positive candidates, not just failures.

2. Specify semantic output-correctness validator.
   - Output: `MAP_System/artifacts/planning/map-semantic-validator-spec.md`.
   - Split deterministic Layer 1 checks from fuzzy Layer 2 judging.
   - Define cited/checkable reason requirements, labeled false-positive data,
     confidence thresholds, and review/adjudication flow.
   - State explicitly: Layer 1 coverage raises catch rate but does not drive
     Layer 2 false positives toward 1%; the false-positive target depends on
     fuzzy judge accuracy, threshold calibration, and adjudicated examples.

3. Add compliance and validator telemetry.
   - Track violation type, sender, thread, task, and adjudication
     (`true_positive`, `false_positive`, `waived`).
   - Track semantic false positives separately from protocol format
     violations.

4. Add halt state.
   - A small shared halt file or DB table blocks runner/agent-loop dispatch
     when a validator records a blocking anomaly.
   - Halt requires root-cause or repair record before release.

5. Add eager-halt rules with accuracy controls.
   - Deterministic Layer 1 failures halt immediately.
   - Fuzzy Layer 2 findings require cited, checkable reasons.
   - False positives are tracked as first-class calibration data.
   - Do not raise the threshold to preserve trust; fix accuracy instead.

### Wave 5: Gap Scoring, Emergence, And Local Lanes

Candidate tasks:

1. Add task classification metadata.
   - Fields: `gap_score`, `task_tier`, `local_lane`, `escalation_reason`.
   - Promotion gate checks required fields for new tasks.

2. Extend `intake_request.py` to emit a gap/classification packet.
   - Low-gap mechanical work can be routed to local helper lanes.
   - High-gap work gets core-agent review and optional emergence suggestions.

3. Add emergence preflight suggestions.
   - Capability pass and coverage pass produce a bounded suggestions list.
   - Suggestions are not silently added unless confidence and policy allow it.

4. Add local-helper lane wrappers.
   - Lanes: repo scan, JSON/schema check, event digest, validator log summary,
     markdown cleanup, acceptance-criteria draft.
   - Every local output remains draft-only and records model, inputs, and owner.

5. Add bounded learning guard.
   - Learned emergence heuristics that fire but do not prevent real defects are
     pruned.
   - Outcome feedback can override validator-only learning signals.

### Wave 6: Outcome Feedback And Knowledge Layer

Candidate tasks:

1. Add outcome event type.
   - Records whether shipped work actually worked in later use.
   - Validation pass and outcome pass remain distinct signals.

2. Add validator blind-spot metric.
   - "Passed validation, failed in reality" becomes a tracked metric and a
     prompt for deterministic validator improvements.

3. Measure Library layer viability.
   - Check real compression ratio, detail-needed rate, and file churn on MAP
     docs before building.

4. Run Research System pass on external Library/tool candidates.
   - Evaluate `iurykrieger/claude-bedrock` and `ccf/agentcairn` as direct
     librarian-bot blueprints.
   - Evaluate the knowledge-graph-driver-RAG hop-limit/token-budget-cap
     pattern.
   - Evaluate `WenyuChiou/agent-collab-skills` acceptance gate against MAP's
     validator/halt design.
   - Evaluate `milisp/codexia` for git worktree/locking lessons.
   - No adoption decision without a Research Summary and measurement plan.

5. Build Library layer only as full design.
   - Compact summaries, wikilinks to full detail, and event-driven staleness
     invalidation land together.
   - Summary-only implementation is explicitly forbidden.

### Wave 7: Resilience Controls

Candidate tasks:

1. Add idempotency registry.
   - MAP write helpers accept an idempotency key and ignore duplicate retries.

2. Add dead-letter queue.
   - Failed dispatches, failed helper attempts, or repeated agent-loop failures
     land in `MAP_System/dead_letters/` or a DB table with replay policy.

3. Add durable/resumable execution.
   - Long tasks emit checkpointed steps.
   - Restart scans the event log for last completed step.
   - Resume uses idempotency keys to avoid double-applying partial writes.
   - Defer broad rollout until real task duration justifies it.

4. Add circuit breakers.
   - Repeated failure by agent/subsystem changes routing status to
     temporarily unavailable until reviewed.

5. Add chaos tests.
   - Kill an agent-loop handler mid-task.
   - Simulate stale task mirror.
   - Simulate malformed hcom/protocol output.
   - Simulate hung/silent agent and heartbeat reaper.
   - Simulate mid-task restart and resume.
   - Simulate committed poisoned state and validate rollback/reconcile path.
   - Confirm detection and containment.

6. Add degradation policy.
   - Validator unavailable: fail closed.
   - Cloud unavailable: continue only local-eligible work.
   - Canonical store unavailable: block writes, allow safe reads from snapshot.
   - Operator absent: hold gated actions, continue ungated work.

7. Add dependency DAG support.
   - Decomposer emits dependency edges.
   - Validator rejects cycles and unresolved dependencies.

### Wave 8: Governance Enforcement

Candidate tasks:

1. Build pre-dispatch policy checker.
   - Reads `AGENT_PERMISSION_LEVELS.md`,
     `DESTRUCTIVE_ACTION_POLICY.md`, `DECISION_CLASSES.md`, and risk class.
   - Emits allow, require approval, or reject.

2. Wire destructive-action gates before work starts.
   - High-risk operations cannot be assigned as ordinary implementation tasks
     without an approval gate.

3. Add capability whitelist tests.
   - Verify helpers cannot be assigned final review, final decision, broad
     architecture, broad file rewrites, or destructive operations.

4. Write threat model.
   - Covers repo, shell, filesystem, local helpers, compression/memory proxies,
     MCP/connectors, and hcom control surfaces.

### Wave 9: Formal Verification And Failure Taxonomy

Candidate tasks:

1. Create a TLA+ research/implementation spike.
   - Output: formal spec or, if tool install is not approved, a design note
     plus executable state-machine tests.
   - Scope: allocator, task claim, git lock; 2-3 abstract agents.

2. Build MAST-style MAP failure coverage matrix.
   - Output: `MAP_System/artifacts/audits/map-failure-taxonomy-coverage.md`.
   - Map each failure class to an existing validator/test or a missing test.

3. Add regression tests for uncovered categories.

4. Assess multi-project reality.
   - Output: `MAP_System/artifacts/audits/map-multi-project-readiness.md`.
   - Cover Pathwell plus at least one other project shape.
   - Identify state that must be global vs. project-local.
   - Identify cross-project resource contention and isolation risks.

5. Assess roster composition.
   - Output: `MAP_System/artifacts/audits/map-roster-composition.md`.
   - Compare two-tier vs. three-tier routing, and agent count per tier.
   - Use real local-helper and core-agent observations where available.
   - Do not register new core/local agents from this assessment alone.

6. Red-team design assumptions.
   - Output: `MAP_System/artifacts/audits/map-613-assumption-red-team.md`.
   - Challenge the assumptions behind the master plan, not only the numeric
     parameters.
   - Include at least one reviewer/helper not involved in writing the plan.
   - Findings become Research, Risk, Self-Repair, or task backlog items.

## Measurement Rules

Every implementation task above should record:

- before/after friction or failure measure where possible;
- validator false-positive count if it adds validation;
- whether it reduced hcom chatter or added new chatter;
- whether it made the shared state more directly readable;
- rollback path.

This is the guardrail against Braess-style intervention backfire.

## Research And Verification Rules

- Treat the 6.13 notes as design input, not final external evidence.
- If a task depends on a current external fact, library behavior, paper claim,
  or GitHub project comparison, route it through the Research System.
- Do not invent sample research artifacts merely to exercise the system.
- Prefer tests and validators over additional policy text when behavior is the
  actual missing piece.

## Immediate Next Steps

1. Wait for `claude-lab-zera` helper findings and merge any contradictions or
   missing high-priority candidates into this plan.
2. Promote this draft into explicit TASK-147+ records.
3. Start with Wave 1 and Wave 2 before adding more validators, because
   enforcement needs one entry point and observable traces.
4. Keep helpers bounded:
   - Zera/helper lane: duplicate/prototype corroboration.
   - Core implementation owners: one task at a time.
   - Local/Ollama helpers: draft-only scans or summaries after a task exists.

## Open Questions

- Should the command-center single entry point be enforced socially first
  through hcom/Monitor conventions, or mechanically in the CommandCenterUI?
- Should halt state live only in SQLite, only in a file, or both with file
  mirrors like tasks?
- Does the operator want TLA+ installed and used directly, or should the first
  formal-verification task produce executable state-machine tests as a lower
  friction substitute?
- Which MATOCP violations should be blocking on day one versus tracked as
  warning telemetry until false-positive rates are known?
