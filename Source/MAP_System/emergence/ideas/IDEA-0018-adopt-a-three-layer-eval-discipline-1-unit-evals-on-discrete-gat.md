# Idea Card

Idea ID: IDEA-0018
Project: MAP
Source insight or synthesis: NONE
Owner: gune
Date: 2026-07-15
Status: CANDIDATE

## Idea


- idea: Adopt a three-layer eval discipline: (1) unit-evals on discrete gate steps, (2) LLM-as-judge regression on agent review/output quality, (3) production trace sampling from events.jsonl; plus a small agent-incident taxonomy (tool-call failure / context truncation / runaway loop).

## Problem or opportunity


- gap: MAP has mechanical gates + peer review but no automated eval harness on its own outputs, and events.jsonl is trace-shaped but not sampled/scored; 2026 industry dominant failure modes (tool-call fail, context truncation, runaway loops) map directly onto RnS/limit-watcher territory.

## Why now


- now: The Command Center Lab is actively testing emergence workflow.

## Expected benefit


- gain: Turns observed failures into regression tests that gate releases; formalizes [[emergence/insights/INS-0021-real-data-contradicts-the-simulation-cut-of-peer-review-reviews-]]'s real-vs-simulation review-yield finding into a standing eval.

## Cost


- cost: Medium: needs an eval fixture set + a judge prompt + events.jsonl span sampling; start lightweight (taxonomy doc + one LLM-as-judge review-quality check).

## Reversibility

- [ ] yes
- [ ] no
- [ ] partial: TBD

## Smallest safe experiment


- test: Create and validate file-backed emergence records.

## Decision needed

- [ ] task-DRI
- [ ] review-DRI
- [ ] state-steward
- [ ] project-DRI
- [ ] human-owner

## Recommendation

- [ ] park
- [ ] reject
- [ ] test
- [ ] promote-task
