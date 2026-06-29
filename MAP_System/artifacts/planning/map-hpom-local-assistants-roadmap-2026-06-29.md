# MAP / HPOM / Local Assistants Roadmap - 2026-06-29

Source: command-center hcom `#8830`.

## Direction

Pause Pathwell work. Focus active development on:

- MAP itself;
- the new HPOM system;
- local AI assistants and how to use them safely inside MAP.

## Current MAP Baseline

- Top-level MAP task graph validates.
- Top-level `run_tests.sh` is documented as passing in current-state, but should be rerun before implementation commits.
- SQLite-backed task claims exist.
- Autonomous agent loop exists and pauses for review/helper proposal routes.
- Local Ollama models and Aider are documented as helper capabilities, not core agents.
- Command-center helper policy requires visible / operator-reachable sessions.

## Immediate Scope

### 1. Stabilize MAP task intake first

Implement strict READY promotion before adding more automation.

Reason:

- Local assistants and HPOM will create more candidate work.
- Candidate work must not become executable until metadata is complete.
- The existing backlog already names this as the high-priority hardening item.

Task shaped: `TASK-035`.

### 2. Add local assistant health checks before wrappers

Implement a read-only health check and capability report before launching wrappers.

Reason:

- `notes/local-model-helper-guide.md` says local assistants are helper-capability-only.
- `notes/command-center-later.md` requires `ollama list`, required model checks, Aider check, and operator-reachability checks before wrappers.
- Health checks create a safe manual workflow and prevent registering local models as core agents prematurely.

Task shaped: `TASK-036`.

### 3. Define HPOM before integrating it

`HPOM` is not defined in the current repository.

Reason:

- No task, note, script, or guideline currently describes HPOM.
- Treating it as HCOM, helper protocol, or a separate orchestration layer would be guessing.
- The Architect/Shaper guide says undefined architecture work should remain shaping work until output paths and acceptance criteria are clear.

Task shaped: `TASK-037`.

## Proposed Dependency Order

```text
TASK-035 strict promotion gate
  -> TASK-036 local assistant health checks
  -> TASK-037 HPOM definition / integration plan
```

HPOM may become independent of `TASK-036` after definition, but for now it should not be wired into local assistant execution until MAP intake and helper visibility checks are safe.

## Local Assistant Operating Rule

Use local assistants for:

- summaries;
- classifications;
- checklist results;
- draft acceptance criteria;
- diff suggestions;
- narrow supervised edits through Aider after baseline safety checks.

Do not use local assistants for:

- final architecture decisions;
- final review approvals;
- broad rewrites;
- ambiguous user-intent decisions;
- hidden background work.

## Open Question

What does `HPOM` stand for in this project, and is it:

- a replacement or layer over HCOM;
- a human-process operating model;
- a helper/protocol/orchestration manager;
- something else?

Until answered, HPOM work should remain `NEEDS_SHAPING`.

## Improvements Checked

Implemented: converted the operator direction into a MAP-side roadmap and shaped concrete next tasks.

Recommended: start with `TASK-035`, because it reduces risk for every later HPOM/local-assistant workflow.

Not changed: Pathwell task statuses, local assistant registration, helper automation, or HPOM implementation.
