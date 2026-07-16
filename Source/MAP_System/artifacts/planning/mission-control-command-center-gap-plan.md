# Mission-Control Command-Center Gap Plan

Status: draft implementation plan
Owner: command-center
Task: TASK-165
Created: 2026-07-14

## Purpose

This artifact compares the current MAP command-center surface with the
6.13 command-center restructuring notes and turns the remaining gap into
bounded implementation increments. It focuses on MAP-owned command-center
work. The external UI project at `/home/home/Projects/CommandCenterUI`
is explicitly out of scope unless the operator approves work outside this
repository's writable roots.

## 6.13 Target

The 6.13 notes define the command center as the structural pivot of MAP:

- Single entry point: the operator states intent once to an orchestrator;
  workers receive protocol-shaped tasks, not raw operator messages.
- Mechanical orchestrator: interpret, validate, decompose, and route;
  keep the role narrow to reduce bottleneck and misinterpretation risk.
- Visibility: one place reconstructs task/agent causal state without
  asking agents for status.
- Governance: high-risk or irreversible actions pass pre-dispatch
  approval gates before execution.
- Operator control surface: show route, queues, halts, validators,
  agent state, and review/approval pressure without making the operator
  reconstruct state from hcom chatter and logs.

## Current MAP State

| Capability | Status | Evidence |
|---|---|---|
| Single intake | Partial | `scripts/intake_request.py` exists and produces structured dispatch packets, but the operator can still message agents directly in live hcom sessions. |
| Mechanical route computation | Implemented | `graph/runner.py` reads canonical state and reports route, queues, policy gates, halt state, helper candidates, and reviewer pressure. |
| Canonical task state | Implemented | `map.db`, `tasks/TASK-NNN.json`, and `workflow/task_graph.json` are kept in sync by export and mirror validators. |
| Pre-dispatch gates | Implemented | `scripts/pre_dispatch_policy.py` plus claim/runner integration block destructive, authority, security, and unbounded helper work before claim. |
| Halt visibility | Implemented | `scripts/halt_state.py` and runner output expose global/task halt state. |
| Agent liveness surface | Partial | `scripts/liveness_reaper.py` writes `shared/liveness-state.md`; the mission-control TUI reads it, but stale hcom data can still make many agents look suspect until the runtime status loop is refreshed. |
| Mission-control dashboard | Partial | `scripts/mission_control_tui.py` and `_mission_control_app.py` provide a read-only curses dashboard. TASK-164 extends it with policy gate/rejection, drift, and dead-letter pressure. |
| One-view causal trace | Partial | `events/events.jsonl` is structured and validated, but not every event carries a trace ID/parent event chain. |
| Operator interventions | Missing by design | Approve/reject, replay dead letter, nudge/resume, kill/suspend, budget bump, and false-halt override are documented as disabled in the first prototype. |
| External graphical CommandCenterUI | Not MAP-owned here | Current external project path is `/home/home/Projects/CommandCenterUI`; this repo stores provenance and MAP-side artifacts only. |
| Textual/k9s-style terminal UI | Approval-blocked | The first prototype uses `curses` because `textual` was not available and would require an external package install approval. |

## What TASK-164 Improves

TASK-164 is the first hardening pass after the read-only prototype:

- Flight board includes dispatch-blocked, policy-gated, and
  policy-rejected queues.
- Attention queue includes policy gate/rejection reasons from runner
  `policy_results`.
- Source drift and dead-letter queue pressure surface as explicit
  attention items.
- Dead-letter queue read errors are visible instead of silently producing
  a blank or misleading panel.
- The read-only/no-write structural tests remain in place.

TASK-164 does not add write-capable controls and does not attempt a Textual
or external CommandCenterUI port.

## Remaining Gap

### 1. Single Entry Point Is Procedural, Not Enforced

Agents can still receive raw operator messages. The system has intake and
dispatch machinery, but there is no command-center gate that mechanically
turns operator chat into a task packet and prevents direct fan-out.

Next increment:

- Add a command-center intake wrapper that accepts operator intent, runs
  `intake_request.py`, writes the resulting packet/event, and prints the
  next runner route.
- Add protocol validation for the wrapper's hcom output shape.
- Keep this as a MAP CLI first; do not alter hcom itself.

### 2. Dashboard Has No Drilldown Model

The TUI shows dense panels, but keybindings for task view, agent roster,
event stream, and attention focus are no-op placeholders.

Next increment:

- Add read-only focus state and drilldown panes for selected task,
  selected agent, and selected attention item.
- Task drilldown should show task status, owner, output paths,
  criteria, last events, policy result, and halt/dead-letter references.
- Agent drilldown should show liveness evidence, claimed task, hcom
  status age if available, and relevant recent events.

### 3. Causal Trace Is Still Thin

The 6.13 simulation expects one view to explain why a halt or reroute
happened. Events are structured, but trace IDs and parent event IDs are not
yet universal.

Next increment:

- Define a minimal `trace_id` convention for task lifecycle events.
- Add trace fields to new events emitted by `map_task.py`,
  `agent_loop.py`, runner/route recording, liveness reaper, and
  dead-letter queue.
- Extend mission-control event rendering to group by trace when present
  while still tolerating legacy events.

### 4. Interventions Are Missing, And That Is Correct For Now

The operator-control actions are intentionally disabled until read-only
state is accurate. Turning them on prematurely would make the TUI a second
dangerous write surface.

Next increment:

- Create a write-control design before any implementation.
- Each control must call a sanctioned command or helper:
  approve/reject through `map_task.py`, dead-letter replay through
  `dead_letter_queue.py`, hcom nudge through `hcom send`, halt clear
  through `halt_state.py`, and budget changes through cost governance.
- Every action must have dry-run/preview, confirmation text, event
  logging, and validator checks after execution.

### 5. External UI Boundary Needs A Decision

MAP currently improves the command-center backend and TUI surface in this
repo. The standalone UI lives outside the writable project root.

Next increment:

- If the operator wants the external UI improved, create a separate task
  with explicit approval to work in `/home/home/Projects/CommandCenterUI`.
- Otherwise keep the MAP-side TUI as the canonical command-center surface
  until its read-only and control-plane contracts are proven.

## Recommended Task Sequence

1. TASK-166 candidate: read-only mission-control drilldowns.
   Output: `mission_control_tui.py`, `_mission_control_app.py`,
   `test_mission_control_tui.py`.

2. TASK-167 candidate: command-center intake wrapper.
   Output: a MAP CLI wrapper plus tests that route operator intent through
   `intake_request.py`, protocol validation, and runner state.

3. TASK-168 candidate: trace ID propagation for new task lifecycle events.
   Output: event schema notes, event emitters, validator tests, and
   mission-control trace grouping.

4. TASK-169 candidate: write-control design, not implementation.
   Output: an artifact specifying sanctioned commands, confirmation gates,
   post-action validators, and rollback/non-rollback expectations.

5. TASK-170 candidate: external UI boundary decision.
   Output: either an operator-approved task for
   `/home/home/Projects/CommandCenterUI` or a decision record that MAP TUI
   remains the active command-center surface for this phase.

## Non-Goals For The Next Increment

- Do not install `textual` without operator approval.
- Do not add write-capable TUI actions before the write-control design is
  reviewed.
- Do not edit the external CommandCenterUI project from this MAP task.
- Do not replace hcom; wrap and structure command-center use of it first.

## Practical Answer

The command center has improved materially against 6.13: the task router,
pre-dispatch gates, halt state, liveness state, event validation, and
read-only mission-control dashboard now exist and are tested. It is not
yet the final 6.13 command center because direct operator-to-agent contact
is still possible, drilldowns are shallow, causal trace is incomplete, and
operator interventions remain disabled by design.
