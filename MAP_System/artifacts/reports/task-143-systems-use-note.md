# TASK-143 Systems-Use Note

task_id: TASK-143
owner: codex-lab-veto
date: 2026-07-04
scope: answer the operator's question about whether MAP is using all available
systems and whether Emergence/Insights and Research need immediate improvement

## Answer

MAP is not using every documented system equally, and it should not force that
as a goal. The healthy pattern from TASK-129, TASK-140, and TASK-141 is that a
system should become mandatory only when a gate, script, or recurring workflow
makes it useful in the normal path.

## Emergence / Insights

Emergence/Insights is active and improving:

- release requires "Emergence capture considered" through `release_task.py`;
- recent real insights were captured and promoted, including the no-self-review
  helper-routing gap;
- TASK-141 found and fixed a real `map_emergence.py` concurrent ID allocation
  bug with `fcntl.flock`.

Immediate need: no broad redesign. The useful improvement path is focused
hardening when failures appear, like TASK-141's ID allocation repair.

## Research

Research is documented and validated, but mostly unexercised. That is not
automatically a failure. Many recent MAP tasks were local implementation,
process, and review work where the sources of truth were repo files, tests, and
live command output.

Immediate need: do not force Research briefs into ordinary implementation
tasks. Use the Research System when work depends on sourced external facts,
current facts, disputed claims, unfamiliar technology choices, or decisions that
will become durable project truth.

## Other Systems

The systems currently showing real operating value are the ones with a
mechanical path:

- task/review/release gates;
- no-self-review;
- security second pass;
- Emergence release consideration;
- Self-Repair records for concrete fixes;
- now, task mirror reconciliation through `validate_task_mirrors.py`.

Systems that remain specification-only should be treated as available tools,
not as box-checking obligations. The next improvements should turn recurring
manual steps into small gates or scripts, not add more prose-only process.
