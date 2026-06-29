# HPOM Scope Definition

Task: `TASK-037`
Status: implemented for review

## Definition

HPOM means Human-Paced Orchestration Model in this MAP implementation.

Canonical live reference:

- `MAP_System/shared/hpom.md`

Worker-fit reference:

- `MAP_System/shared/agent-capability-matrix.md`

Durable decision:

- `MAP_System/shared/decisions.md` DEC-011

## Boundary

HPOM is not a replacement for MAP. It does not own durable task state,
claiming, event storage, approval gates, or file memory.

HPOM is the assignment layer that decides which worker type should handle a
piece of work before MAP execution begins or helper work is delegated.

## Outputs Created

- `shared/hpom.md`
- `shared/agent-capability-matrix.md`
- `shared/architecture.md` HPOM section
- `shared/current-state.md` HPOM status
- `shared/decisions.md` DEC-011

## Review Notes

Review should check:

- whether the HPOM definition is clear enough for future agents;
- whether the capability matrix prevents token-wasteful helper assignment;
- whether local assistants remain draft-only and non-authoritative;
- whether the implementation order protects MAP before adding wrappers.

## Improvements Checked

Implemented: HPOM has a concrete operating definition, authority tiers, routing questions, and worker-fit matrix.

Recommended: implement `TASK-035` and `TASK-036` before adding any local assistant launch wrappers.

Not changed: helper automation, local model registration, Aider wrapper behavior, or core-agent list.
