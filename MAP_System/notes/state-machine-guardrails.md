# State Machine Guardrails

## Status

- Proposal: `open`
- Priority: `high`
- Related issue: approved tasks with missing metadata break validation.

## Existing Foundation

- SQLite `tasks.status` already exists.
- `db/claims.py` only claims tasks with `status = 'READY'` or expired
  `IN_PROGRESS` leases.
- `validate_task_graph.py` already detects missing `acceptance_criteria` and
  `output_paths`.

## Gap

MAP does not yet enforce metadata completeness at the transition into `READY`.

Broken tasks can exist with executable-looking statuses, then fail validation
later.

## Principle

Be conservative in what MAP accepts from agents.

Do not let LLM-authored task records become executable until metadata passes a
strict pre-flight gate.

## Proposed Task States

```text
BACKLOG
  raw idea or incomplete task metadata

NEEDS_SHAPING
  task exists but needs Architect/Shaper metadata work

READY
  metadata complete and dependencies satisfied enough for claiming

IN_PROGRESS
  claimed by one agent with an active lease

SUBMITTED
  implementation complete, awaiting review

CHANGES_REQUESTED
  review found required fixes

APPROVED
  independently approved

BLOCKED
  cannot proceed without external input or decision
```

## Required READY Gate

A task may enter `READY` only when:

- `task_id` is present;
- `title` is non-empty;
- `description` is non-empty;
- `task_type` is present;
- `role` is present;
- `dependencies` is a list;
- `input_paths` is a list;
- `output_paths` has at least one entry;
- `acceptance_criteria` has at least one concrete entry;
- task file exists at `tasks/TASK-NNN.json`;
- `workflow/task_graph.json` contains matching task data.

## Claim Gate

Execution agents may only claim:

- `status = 'READY'`;
- metadata passes the READY gate;
- dependencies are terminal or otherwise allowed by policy;
- required agent, if any, is available.

## Implementation Options

### Option A: Strict Promotion Script

Create:

```text
scripts/promote_task.py
```

Responsibilities:

- validate task file;
- sync SQLite and file mirrors;
- refuse `READY` transition on missing metadata;
- emit an event with pass/fail reason.

### Option B: SQLite Trigger

Add database triggers that reject `status = 'READY'` when related output paths
or acceptance criteria are missing.

Tradeoff:

- stronger enforcement;
- harder to debug and migrate than script-level checks.

### Option C: Claim-Time Defense

Update `claim_task()` to refuse READY tasks missing output paths or acceptance
criteria.

Tradeoff:

- protects execution loop;
- still allows invalid READY state to exist.

## Recommended Path

Implement in this order:

1. Script-level promotion gate.
2. Claim-time defense.
3. Optional SQLite triggers after behavior stabilizes.

## Pushback

Do not start with SQLite triggers unless script-level behavior is already proven.

Risk:

- trigger failures are harder for agents to diagnose;
- schema changes are harder to reverse;
- strict database enforcement can block repair work if the transition model is
  wrong.

Safer path:

- make validation failures readable first;
- add tests around promotion and claiming;
- add triggers only after the state machine has stabilized.

## Event Types

Use:

- `TASK_SHAPING_REQUIRED`
- `TASK_METADATA_VALIDATED`
- `TASK_READY_REJECTED`
- `TASK_PROMOTED_READY`

## Open Follow-Up

- Task: create implementation task for `scripts/promote_task.py`.
- Task: update `map_task.py create` so new tasks default to `BACKLOG` unless
  metadata is complete.
- Task: add tests for invalid metadata, valid promotion, and claim-time defense.
