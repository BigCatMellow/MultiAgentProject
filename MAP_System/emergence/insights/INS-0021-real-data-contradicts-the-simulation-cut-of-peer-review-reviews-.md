# Insight Record

Insight ID: INS-0021
Project: MAP
Related task: TASK-188
Detected by: claude-lab-toku
Date: 2026-07-14
Status: RAW

## Short description


- obs: Real data contradicts the simulation cut of peer review: reviews catch 1-in-4.3 submissions pre-release while the semantic validator the cut assumed does not exist; do not weaken the review gate before L2 validator accuracy is measured.

## Trigger


- src: TASK-188 real-parameter calibration: review-catch rate measured at 23.1% (36/156 submissions drew CHANGES_REQUESTED, all recovered pre-release), while zero halts have ever been set and no L2 semantic validator exists.

## The synthesis


- synth: Real data contradicts the simulation cut of peer review: reviews catch 1-in-4.3 submissions pre-release while the semantic validator the cut assumed does not exist; do not weaken the review gate before L2 validator accuracy is measured.

## Why it might matter


- why: The 6.13 simulations cut universal peer review as net-negative conditional on a validator that catches defects; reality has no such validator yet, so the review gate is currently carrying the entire defect-catch load. Weakening review on simulation grounds before L2 lands would remove MAP's only working defect-catch layer.

## Evidence


- ev: [[artifacts/audits/map-real-parameter-calibration-results-2026-07-14]] section 6 (review-catch rate); shared/halt-state.json never set; the three shipped defects (TASK-050/177/179 fixes) got past review, not past a validator.

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
