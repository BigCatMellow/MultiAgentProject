# MAP Emergence Learning Guard Spec (TASK-153, Wave 5)

Status: draft-active
Owner: command-center
Built by: TASK-153

## Purpose

Round 5 showed the emergence learning loop can converge, but also that
unguarded learning over-learns from misattributed defects. This spec defines
the pruning guard: learned heuristics must prove they prevent real defects,
not merely fire often or satisfy validators.

## Learned Heuristic Record

Each learned heuristic should record:

| Field | Meaning |
|---|---|
| `heuristic_id` | Stable identifier. |
| `source_event` | Defect, review finding, repair, or outcome that created it. |
| `claim` | What the heuristic predicts or prevents. |
| `trigger` | Task features that cause it to fire. |
| `recommended_action` | What it asks the agent to do. |
| `fires` | Count of times triggered. |
| `prevented_defects` | Count of later real defects prevented. |
| `false_fires` | Count of firings with no observed benefit or added cost. |
| `last_evaluated` | Timestamp/date of last guard pass. |
| `status` | `candidate`, `active`, `pruned`, `needs_review`. |

## Pruning Rule

Prune or demote a heuristic when it repeatedly fires without preventing real
defects.

Default rule:

- after 3 firings, require at least 1 credible prevented defect or review
  finding avoided;
- after 5 firings with zero benefit, mark `pruned`;
- if the heuristic adds cost or scope to every task, lower the threshold for
  review;
- if evidence is ambiguous, mark `needs_review`, not `active`.

## Outcome Feedback Beats Validator-Only Learning

Validator results are useful but incomplete.

Priority order:

1. Real outcome: shipped work later worked or failed in practice.
2. Independent review: a reviewer found or did not find the defect class.
3. Repair record: recurring drift/root-cause evidence.
4. Validator pass/fail.
5. Heuristic self-report.

If a heuristic fires and validators pass but the real outcome later fails,
the outcome wins. If validators complain but repeated real outcomes show the
heuristic does not prevent defects, prune or revise it.

## Misattribution Control

A defect can be blamed on the wrong cause. Learned heuristics must therefore
carry attribution confidence:

| Confidence | Treatment |
|---|---|
| `high` | Direct evidence ties cause to defect; may become active. |
| `medium` | Plausible but not proven; stays candidate until more evidence. |
| `low` | Capture as insight only; do not route tasks based on it. |

No heuristic learned from a single low-confidence attribution should become
active.

## Guard Pass

Run a guard pass during retrospectives or outcome-feedback review:

1. List active heuristics.
2. Count firings since last evaluation.
3. Link each firing to outcome/review/repair evidence.
4. Mark prevented defects.
5. Mark false fires and added-cost cases.
6. Prune, demote, or keep.
7. Record the decision in an emergence artifact or review note.

## What Gets Pruned

Prune:

- heuristics that only add boilerplate;
- suggestions that repeatedly add output paths without preventing defects;
- local-helper lanes that produce rework more often than value;
- validator-derived rules that correlate with warnings but not real failures;
- preflight suggestions that repeatedly distract from scoped work.

Keep:

- heuristics that prevented review findings;
- heuristics tied to recurring repairs;
- heuristics that reduce operator approvals without hiding risk;
- heuristics that route low-gap work to cheaper lanes with no quality loss.

## Relationship To Round 5

Round 5 found the unguarded loop accumulates permanent spurious heuristics as
misattribution rises. The guarded loop prunes heuristics that fire repeatedly
without preventing defects and stays stable under realistic noise. MAP should
therefore default the guard on, even if it adds slight overhead in very low
noise conditions.

## Release Discipline

A heuristic can affect dispatch only after:

- it has a record;
- it has attribution confidence;
- it has a review owner;
- it has a pruning condition;
- it can be overridden by outcome feedback.

Anything less is an insight or candidate idea, not routing policy.
