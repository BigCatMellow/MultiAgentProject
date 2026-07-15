# Idea Card

Idea ID: IDEA-0020
Project: MAP
Source insight or synthesis: NONE
Owner: gune
Date: 2026-07-15
Status: CANDIDATE

## Idea


- idea: Two-pizza ownership metrics: give each agent/lane a well-defined metric set and full responsibility for its area, surfaced in map_metrics.py + the CommandCenterUI card, per Amazon's two-pizza principle (small autonomous teams measured by clear metrics, owning all aspects).

## Problem or opportunity


- gap: MAP has system-wide metrics (map_metrics.py) but light per-agent accountability; two-pizza model ties autonomy to a defined metric set + end-to-end ownership.

## Why now


- now: The Command Center Lab is actively testing emergence workflow.

## Expected benefit


- gain: Clearer accountability and idle/throughput visibility per agent; complements declared-idle (TASK-084) and RnS.

## Cost


- cost: Medium: define the per-agent metric set, extend map_metrics.py aggregation, add a UI row; risk of gaming/noise if metrics chosen badly.

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
