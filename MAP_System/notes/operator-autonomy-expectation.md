# Operator Autonomy Expectation

Date: 2026-07-14
Source: command-center hcom message during MAP 6.13 implementation-task drafting

## Rule

When command-center gives MAP agents a task, agents should continue the work
autonomously without requiring repeated operator bumps or routine approvals.

Agents should ask command-center only for true blockers, operator decisions,
scope/privacy risks, destructive approvals, or downloads/external installs.
For downloads/external installs, state what is needed and what it is for, then
wait for approval.

Routine implementation, validation, task creation, review routing, and
mechanical coordination should proceed through the existing MAP/hcom rules
without asking the operator to confirm every step.

## Operational Effect

- Prefer durable MAP files and hcom `inform` progress over hcom `request`.
- Do not pause merely because the next step is obvious and within current
  authority.
- Continue from runner/task state unless blocked by policy, missing tools,
  failed validation, or an explicit pause.
- Keep visible helper tabs for helper/reviewer work; do not use headless
  helpers unless command-center explicitly instructs it.
