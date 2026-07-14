# MAP Dependency DAG Spec (TASK-155, Wave 7)

Status: draft-active
Owner: command-center
Built by: TASK-155

## Purpose

MAP tasks already carry `dependencies`, and `validate_task_graph.py` already
rejects unknown dependencies and cycles. This spec defines the next contract
for dependency edges emitted by the decomposer and consumed by runner,
validators, and future resilience controls.

This is a design artifact only. TASK-155 does not change the task schema.

## Current Baseline

Current behavior:

- task graph stores `dependencies` as task IDs;
- runner treats `DONE`, `APPROVED`, and `RELEASED` as dependency-satisfied;
- `READY` tasks with unsatisfied dependencies appear as blocked;
- validator rejects unknown dependency IDs;
- validator rejects dependency cycles;
- validator checks active output path collisions.

The next step is to make dependency intent explicit enough for decomposer,
review, and quarantine behavior.

## Decomposer-Emitted Edges

When the decomposer creates a task graph, it should emit dependency edges with
metadata before storing the simplified task-level `dependencies` list.

Recommended edge fields:

| Field | Meaning |
|---|---|
| `from_task_id` | Upstream task that must complete first. |
| `to_task_id` | Downstream task waiting on the upstream task. |
| `edge_type` | `artifact`, `decision`, `validation`, `review`, `release`, or `data`. |
| `required_status` | Minimum upstream status: normally `APPROVED`; sometimes `DONE` or `RELEASED`. |
| `artifact_paths` | Paths the downstream task expects to consume. |
| `reason` | Human-readable reason for the dependency. |
| `optional` | Boolean; optional edges do not block readiness but should be visible. |
| `created_by` | Decomposer or agent that emitted the edge. |

The existing task `dependencies` field remains the compatibility projection:
all non-optional edges become upstream task IDs in `to_task.dependencies`.

## Edge Types

| Edge type | Meaning | Typical required status |
|---|---|---|
| `artifact` | downstream consumes upstream output paths | `APPROVED` |
| `decision` | downstream needs an authority decision or policy choice | `APPROVED` or `RELEASED` |
| `validation` | downstream depends on validator/test result | `DONE` or `APPROVED` |
| `review` | downstream is review/fix after implementation | `SUBMITTED` for review routing, `APPROVED` for follow-on work |
| `release` | downstream requires released canonical state | `RELEASED` |
| `data` | downstream depends on imported or generated data | `APPROVED` |

If edge metadata is absent, runner keeps current behavior: dependencies are
satisfied by `DONE`, `APPROVED`, or `RELEASED`.

## Validation Rules

Required validator behavior:

- reject a dependency edge whose upstream or downstream task ID is unknown;
- reject cycles across non-optional edges;
- warn on optional-edge cycles because they can confuse visualization;
- reject self-dependency;
- reject duplicate edge records unless metadata is identical;
- reject dependencies on `RETIRED` tasks for non-optional edges;
- reject unresolved artifact dependencies where `artifact_paths` are listed
  but not owned by the upstream task output paths;
- reject active output collisions except for declared shared outputs;
- include the cycle path or unresolved task/path in the error.

Cycle example:

```text
TASK-201 -> TASK-204 -> TASK-209 -> TASK-201
```

Unknown dependency example:

```text
TASK-204 depends on TASK-999, but TASK-999 is not defined.
```

Unresolved artifact example:

```text
TASK-204 consumes MAP_System/foo.md from TASK-201, but TASK-201 does not
declare that path in output_paths.
```

## Runner Semantics

Runner should continue computing readiness from task rows, but future edge
metadata allows more precise routing:

- required non-optional edges block readiness until satisfied;
- optional edges appear in route state but do not block dispatch;
- quarantined upstream outputs block only downstream tasks that consume them;
- dead-lettered upstream tasks block downstream tasks and surface a repair or
  replay route;
- required agent unavailability remains separate from dependency satisfaction.

If `required_status` is stricter than the current dependency-satisfied set,
runner should use the stricter requirement for that edge. For example, a
release edge should not become ready when the upstream task is only `DONE`.

## Decomposition Guidelines

The decomposer should create edges when:

- one task reads or edits outputs from another task;
- a review task needs an implementation task submitted first;
- a policy task requires prior research or authority decision;
- a release task needs all implementation and review tasks approved;
- a repair task depends on validation evidence.

The decomposer should not create edges merely because two tasks are in the
same wave. Overbroad dependencies reduce parallelism and make dead-letter
recovery harder.

## Resilience Integration

Dependency metadata supports blast-radius containment:

- artifact quarantine blocks only tasks with matching artifact edges;
- task quarantine blocks tasks with non-optional edges from that task;
- dead-letter replay can identify downstream tasks that need revalidation;
- cycle/unresolved-dependency validator failures fail closed for graph writes.

When a committed poisoned state is detected, the repair record should list
downstream tasks reached through dependency edges so reviewers can assess
cascade risk.

## Migration Path

1. Keep current `dependencies` list as the authoritative blocking field.
2. Add optional edge metadata in a future table/file while preserving export.
3. Update decomposer to emit metadata and projection together.
4. Extend validator to compare metadata against task output paths.
5. Extend runner to honor `required_status` and quarantine scope.

No implementation should remove the simple task `dependencies` field until all
tools read the edge metadata.
