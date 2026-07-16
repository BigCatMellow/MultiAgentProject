# Experiment Record

Experiment ID: EXP-0001
Project: MAP
Source idea: IDEA-0009
Owner: claude-lab-mira
Date: 2026-07-14
Status: PROPOSED

## Hypothesis


- hyp: Dry-run suppression check: treat inactive/session_superseded and inactive/disposable_session_ended as terminal in the limit watcher, replay current watcher state + hcom snapshot, verify no probes/incidents/resumes for terminal sessions and that every suppression is visible in dry-run output

## Test


- test: Run the bounded command or workflow described by this record.

## Scope


- scope: Only the files and artifacts named in this record.

## Limits


- limits: Do not bypass HPOM task, review, or release gates.

## Success criteria


- pass: The record produces useful evidence without expanding scope.

## Failure criteria


- fail: The record is unclear, unused, or creates unsafe ambiguity.

## Evidence to collect

- ev: baseline --once --dry-run (2026-07-14, pre-change): watcher would probe claude-lab-zera and codex-lab-mozu — both sessions ended on purpose same day (librarian batches / TASK-175-178 done). Live reproduction of IDEA-0009's failure mode. Saved: scratchpad task186-baseline-dryrun.txt; contents to be copied into MAP_System/artifacts/tests/task-186-rns-suppression-evidence.md.
- ev: post-change dry-run after terminal marks applied (pending — helper claude-lab-zero implementing per inbox/helpers/task-186-rns-terminal-suppression-implementer.md).

## Review path

- review: TASK-186 (owner claude-lab-mira); implementation by visible helper claude-lab-zero under owner accountability; independent review by codex-lab-nivo at submission.

## Result

- result: pending

## Decision

- [ ] adopt
- [ ] revise
- [ ] reject
- [ ] park

## Notes

- note:
