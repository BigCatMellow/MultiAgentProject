# MAP Outcome Feedback Spec (TASK-154, Wave 6)

Status: draft-active
Owner: command-center
Built by: TASK-154

## Purpose

MAP currently distinguishes task submission, review approval, and validator
passes. Those are necessary but not the same as "the work actually worked
later." Outcome feedback adds a later signal that records real-world result
after use, so validators and reviewers can learn from misses.

This is a design artifact only. TASK-154 does not add event schema or runner
behavior.

## Core Distinction

| Signal | Meaning | Owned by |
|---|---|---|
| `validation_pass` | Deterministic validators/tests accepted the artifact at review time. | validator/test suite |
| `review_pass` | Independent reviewer found no blocking issue against acceptance criteria. | reviewer |
| `outcome_pass` | Later use showed the shipped work behaved as intended. | operator/core agent observing use |
| `outcome_fail` | Later use found a defect, drift, missed requirement, or operational failure. | operator/core agent observing use |

A task can pass validation and review but fail in reality. That case is not a
contradiction; it is the main learning signal this spec exists to capture.

## Outcome Event Shape

Future events should use canonical event validation before adding new event
types. Until an event registry is extended, use `PROGRESS` or
`DECISION_RECORDED` with the fields below in the summary or structured payload
where supported.

Recommended event fields:

| Field | Meaning |
|---|---|
| `outcome_id` | Stable outcome record ID. |
| `task_id` | Task whose output was later exercised. |
| `observed_at` | UTC timestamp of the later observation. |
| `observed_by` | Agent/operator who observed or verified the outcome. |
| `outcome_status` | `pass`, `fail`, `partial`, `unknown`, or `not_exercised`. |
| `use_context` | What later use exercised the artifact. |
| `validation_status_at_ship` | `passed`, `failed`, `waived`, or `not_applicable`. |
| `review_status_at_ship` | `approved`, `changes_requested`, `waived`, or `not_applicable`. |
| `failure_class` | `validator_blind_spot`, `review_blind_spot`, `requirement_gap`, `stale_context`, `integration_gap`, `operator_mismatch`, or `external_change`. |
| `severity` | `COSMETIC`, `DRIFT`, `BLOCKING`, or `STRUCTURAL`. |
| `evidence_paths` | Logs, tests, bug reports, repair records, or follow-up tasks. |
| `follow_up` | `none`, `repair`, `risk`, `validator_improvement`, `research`, or `task_backlog`. |

## Validator Blind-Spot Rate

The validator blind-spot metric is:

```text
validator_blind_spot_rate =
  count(outcome_fail where validation_status_at_ship == passed)
  / count(outcome_known where validation_status_at_ship == passed)
```

Definitions:

- `outcome_known`: a later use produced `pass`, `fail`, or `partial`.
- `outcome_fail`: later use found a real defect or missed requirement.
- `validator_blind_spot`: the artifact passed deterministic validation but
  later failed in a way a future deterministic check could plausibly catch.

Do not include `not_exercised` outcomes in the denominator. A task that nobody
used yet is not evidence that validation worked.

## Review Blind-Spot Rate

Review blind spots are separate:

```text
review_blind_spot_rate =
  count(outcome_fail where review_status_at_ship == approved)
  / count(outcome_known where review_status_at_ship == approved)
```

This distinguishes "the validator missed something mechanical" from "the human
or agent reviewer missed task intent, scope, or judgment."

## Follow-Up Routing

| Outcome failure | Route |
|---|---|
| deterministic validator could catch it next time | validator improvement task |
| stale or contradictory durable state caused it | Self-Repair record |
| standing exposure remains after the incident | Risk register |
| external fact changed or was unverified | Research Summary or refresh |
| task intent was under-specified | decomposer/intake backlog |
| approved artifact needs correction | normal HPOM repair/rework task |

Outcome feedback is not punishment for a reviewer or agent. It is the evidence
source that prevents MAP from learning only from validator pass/fail.

## Storage

Initial implementation should avoid a new opaque store. Prefer one of:

- event records plus derived metrics from `events/events.jsonl`;
- a small SQLite table keyed by `outcome_id`, exported to readable artifacts;
- a periodic metrics artifact produced by `map_metrics.py`.

Outcome records should link to tasks, reviews, repairs, risks, and validators
instead of duplicating full context.

## Validation Path

Implementation tasks should add tests that:

- validation pass and outcome pass are distinct;
- failed later use increments blind-spot counters only when outcome is known;
- `not_exercised` does not inflate success rate;
- failures route to validator improvement, repair, risk, research, or backlog;
- metrics can be computed without scanning chat transcripts.
