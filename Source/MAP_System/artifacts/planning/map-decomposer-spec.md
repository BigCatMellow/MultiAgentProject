# MAP Decomposer Spec

- Status: draft-active
- Task: TASK-147
- Owner: command-center
- Created: 2026-07-13

## Purpose

The decomposer turns an intake packet into one or more executable MAP tasks.
It is the explicit answer to the 6.13 gap that "HPOM interprets intent and
decomposes it" was previously a black box.

## Required Inputs

- operator request text;
- dispatch classification from `scripts/intake_request.py`;
- relevant project routing rules from `AGENTS.md`;
- authority rules from `DECISION_AUTHORITY_SYSTEM.md`;
- permission/destructive-action rules where relevant;
- current task graph and agent availability.

## Required Output Fields

Every decomposed task must define:

- `task_type`;
- `role`;
- `subtasks` or a statement that no split is needed;
- `dependencies`;
- `output_paths`;
- `acceptance_criteria`;
- `risk_class`;
- `approval_gates`;
- `routing_lane`;
- `rollback_expectation`;
- `verification_commands`;
- `reviewer_or_review_path`.

## Dependency Rules

- Dependencies must be explicit task IDs once tasks exist.
- A task must not depend on an informal chat message.
- Cycles are decomposer defects.
- Shared output paths must be serialized through dependencies or split.

## Approval Rules

The decomposer must add an approval gate when the request involves:

- destructive file or Git operations;
- publication or push;
- repo-global changes;
- security or permission policy;
- command-center authority changes;
- irreversible user-facing workflow changes.

## Routing Lanes

| Lane | Use |
|---|---|
| `local` | deterministic checks, summaries, schema scans, draft-only support |
| `core-codex` | implementation and test work |
| `core-claude` | synthesis, architecture, review, research planning |
| `helper-visible` | bounded support with durable helper note |
| `operator` | decision, approval, or scope question |

## Rollback Expectation

Every implementation task should say how to back out:

- no rollback needed, artifact-only;
- revert specific files;
- restore from generated backup;
- run repair/reconcile script;
- operator decision required.

## Acceptance For This Spec

The decomposer is usable when a future agent can take a broad operator request
and produce a task packet without relying on chat memory.
