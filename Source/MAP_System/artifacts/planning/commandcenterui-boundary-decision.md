# CommandCenterUI Boundary Decision

Status: proposed decision
Task: TASK-169
Owner: codex-lab-mozu
Created: 2026-07-14

## Decision

For the next MAP command-center phase, keep implementation work inside the
MAP-side mission-control TUI unless the operator explicitly approves work in
the external CommandCenterUI project.

Default active surface:

```text
MAP_System/scripts/mission_control_tui.py
MAP_System/scripts/_mission_control_app.py
```

External UI path, not currently in scope for MAP task edits:

```text
/home/home/Projects/CommandCenterUI
```

## Why

MAP's canonical working repository is:

```text
/home/home/Projects/MultiAgentProject
```

The current session's writable roots cover this repo, `/home/home/.hcom`, and
temporary paths. CommandCenterUI is a separate codebase with its own runtime
and restart lifecycle. Existing MAP artifacts already document this boundary:

- `MAP_System/artifacts/command-center-ui/README.md` says live
  CommandCenterUI work lives outside this repo and this folder is provenance
  unless a current task points here.
- `MAP_System/artifacts/planning/task-135-projectupdater-commandcenterui-integration-plan.md`
  names the external CommandCenterUI path and records that prior edits there
  required explicit operator approval or writable-root changes.
- `MAP_System/artifacts/planning/map-runtime-migration-inventory.md` says any
  MAP feature expecting a UI surface must treat CommandCenterUI as an external
  consumer with its own migration step, not part of this repo's atomic change
  set.

## Options

### Option A: MAP-Side TUI Remains The Active Surface

Keep building the mission-control TUI in `MAP_System/scripts/`.

Pros:

- Fully inside the current canonical repo and writable task scope.
- Already tested and approved through TASK-160, TASK-164, and TASK-166.
- Can continue proving read-only state, drilldowns, trace grouping, and
  command contracts before adding write-capable controls.

Cons:

- Not the external graphical CommandCenterUI.
- Requires restarting only the TUI process to load code changes, not the whole
  lab.

### Option B: External CommandCenterUI Read-Only Integration

Create a new task that explicitly targets
`/home/home/Projects/CommandCenterUI` for read-only MAP/hcom status display.

Pros:

- Puts state in the operator's existing graphical command-center UI.
- Can reuse the proven MAP-side data contracts from mission-control.

Cons:

- Requires explicit operator approval or a writable-root/session update.
- Needs its own validation and restart plan for the external app.
- Must avoid introducing write controls before the write-control design is
  reviewed and approved.

### Option C: External CommandCenterUI Write Controls

Add approve/reject/replay/nudge/halt-clear/budget controls directly to the
external UI.

Pros:

- Highest operator convenience if implemented correctly.

Cons:

- Not ready. This depends on the write-control design from TASK-168 and on
  read-only external integration being correct first.
- Higher blast radius because it crosses repo and runtime boundaries.

## Recommendation

Choose Option A as the default now.

Use Option B only after the operator explicitly says to work on
`/home/home/Projects/CommandCenterUI` and the task records that external path
as an output boundary. Defer Option C until the write-control design is
approved and read-only CommandCenterUI integration has proven accurate.

## Required Approval Before External Edits

Before any agent edits `/home/home/Projects/CommandCenterUI`, the task must
include all of the following:

- Explicit operator approval naming the external path.
- Output paths for the exact external files to edit.
- A note that the work is outside the canonical MAP repo's normal writable
  scope.
- A validation plan for the external app, including any server restart needed.
- A statement of whether the task is read-only UI integration or write-capable
  control work.
- For write-capable controls, a reference to the approved write-control spec
  and the sanctioned command behind each action.

## Practical Restart Rule

No full Command Center Lab restart is required for MAP-side mission-control
changes. Restart only an already-running `mission_control_tui.py` process to
load changed Python code.

If a future approved task edits the external CommandCenterUI app, that task
must define its own restart command and verification steps.

## Consequence

The command center can keep improving immediately through the MAP-side TUI.
The external CommandCenterUI remains a possible consumer, but not an implicit
implementation target.
