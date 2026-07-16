# Insight Record

Insight ID: INS-0022
Project: MAP
Related task: NONE
Detected by: gune
Date: 2026-07-15
Status: RAW

## Short description


- obs: obs: MAP is a supervisor + durable-blackboard + swarm-handoff hybrid, and the durable file/SQLite blackboard plus mechanical release gates is a real differentiator vs 2026 frameworks (LangGraph/CrewAI/AutoGen) whose coordination state is ephemeral/in-memory.

## Trigger


- src: operator E/I research wave: benchmark MAP against best-in-class multi-agent systems

## The synthesis


- synth: obs: MAP is a supervisor + durable-blackboard + swarm-handoff hybrid, and the durable file/SQLite blackboard plus mechanical release gates is a real differentiator vs 2026 frameworks (LangGraph/CrewAI/AutoGen) whose coordination state is ephemeral/in-memory.

## Why it might matter


- why: Confirms what to protect and lean into: durability + gates are why MAP work actually gets used (see [[emergence/insights/INS-0014-systems-with-a-mechanical-release-task-gate-get-genuinely-used-r]]); most competitors bolt persistence on later.

## Evidence


- ev: Industry consensus: supervisor is 2026 production default; swarm/blackboard use shared state stores (Redis/Postgres); MAP already runs supervisor(orchestrator)+blackboard(tasks/,shared/,events.jsonl,map.db)+swarm(hcom handoffs) with SQLite-arbitrated claims.

## Risk


- risk: Acting without promotion could bypass HPOM governance.

## Scope


- scope: Only the files and artifacts named in this record.

## Recommended next action

- [ ] ignore
- [ ] park
- [ ] task
- [ ] idea
- [ ] experiment
- [ ] escalate-human

## Notes

- note:
