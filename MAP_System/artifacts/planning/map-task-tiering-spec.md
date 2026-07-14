# MAP Task Tiering Spec (TASK-153, Wave 5)

Status: draft-active
Owner: command-center
Built by: TASK-153

## Purpose

Task tiering decides how much authority, review, and model cost a task
deserves. It does not replace HPOM authority: core agents keep ownership of
final integration, and command-center keeps final authority for operator
decisions.

## Fields

Add or emit these fields in future intake/dispatch packets:

| Field | Type | Meaning |
|---|---|---|
| `gap_score` | integer 0-100 | Estimated uncertainty/novelty/risk gap between intent and executable work. |
| `task_tier` | string | Routing tier: `mechanical`, `bounded`, `architecture`, `policy`, `operator`. |
| `local_lane` | string or null | Allowed draft-only local/helper lane, if any. |
| `escalation_reason` | string or null | Why work must escalate to core or command-center. |
| `classification_evidence` | list of strings | Short facts that justify the tier. |

## Gap Score

Scoring dimensions:

| Dimension | Low score | High score |
|---|---|---|
| Intent clarity | concrete file/test request | ambiguous goal or missing acceptance criteria |
| Risk | doc cleanup or schema check | task claims, approvals, security, budget, destructive action |
| Novelty | existing local pattern | new architecture or policy |
| Blast radius | one declared output file | shared runtime, task graph, event schema, multiple projects |
| Reviewability | deterministic pass/fail | judgment-heavy or subjective |
| Local suitability | draft/check/summary | final decision or canonical state mutation |

Suggested bands:

| Score | `task_tier` | Dispatch expectation |
|---|---|---|
| 0-20 | `mechanical` | Local/helper draft is usually safe; core integrates. |
| 21-45 | `bounded` | Core owner with optional helper for narrow checks. |
| 46-70 | `architecture` | Core agent owns; helper may inspect or draft only. |
| 71-90 | `policy` | Core proposal plus command-center approval if policy/authority changes. |
| 91-100 | `operator` | Needs command-center decision before execution. |

## Local Lane Selection

Allowed `local_lane` values:

- `repo_scan`
- `json_schema_check`
- `event_digest`
- `validator_log_summary`
- `markdown_cleanup`
- `acceptance_criteria_draft`

Denied lanes:

- final approval;
- task completion claim;
- broad rewrite;
- policy decision;
- architecture decision;
- direct mutation of canonical MAP state.

## Promotion And Dispatch Expectations

Before a promoted task becomes `READY`, the packet should include:

- `gap_score`;
- `task_tier`;
- `local_lane` or explicit `null`;
- `escalation_reason` when tier is `architecture`, `policy`, or `operator`;
- acceptance criteria;
- output paths;
- owner/integration authority.

Dispatch rules:

- `mechanical`: may start with a local/helper draft if output paths and stop
  condition are explicit.
- `bounded`: may use local lanes for checks/summaries, but a core agent owns
  edits and submission.
- `architecture`: core agent owns; helper only for bounded review, source
  inspection, or alternate draft.
- `policy`: core agent can draft; command-center approval required before
  binding policy/authority changes.
- `operator`: request Issue/Options/Recommendation/Needed before execution.

## Review Expectations

Reviewers should check whether the tier was accurate:

- if a low-tier task required major judgment, raise future score;
- if a high-tier task was purely mechanical, lower future score;
- if a local/helper lane produced useful draft output, record that evidence;
- if a local/helper lane caused rework, feed that into the learning guard.

The score is guidance, not authority. When in doubt, escalate to core review.
