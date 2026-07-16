# MAP Local Helper Lanes Spec (TASK-153, Wave 5)

Status: draft-active
Owner: command-center
Built by: TASK-153

## Purpose

Local helpers reduce paid-model load by doing bounded draft/check/summary
work. They are never final authority, never hidden background workers, and
never owners of task completion.

## Lane Contract

Every local/helper invocation records:

- owning core agent;
- task ID or reason;
- model/tool;
- lane;
- input paths;
- output path;
- stop condition;
- review owner.

Use `scripts/local_runner.py` and `inbox/helpers/` for durable records when
using Ollama/local helpers.

## Allowed Lanes

| Lane | Model fit | Output type | Stop condition |
|---|---|---|---|
| `repo_scan` | small summarizer | candidate files and short rationale | list of paths plus uncertainty |
| `json_schema_check` | local coder | schema/checklist result | pass/fail with exact fields |
| `event_digest` | summarizer | event summary | bounded time/window summary |
| `validator_log_summary` | summarizer/coder | failure digest | exact failing commands and likely file |
| `markdown_cleanup` | cleanup model | draft text edits | no meaning change, diff suggestion only |
| `acceptance_criteria_draft` | reasoning model | draft criteria | binary criteria proposal |

## Draft-Only Rule

Local/helper lanes may produce:

- summaries;
- classifications;
- checklist results;
- draft criteria;
- diff suggestions;
- recommendations.

They may not produce:

- final approval;
- final architecture decision;
- task completion claim;
- unbounded rewrite;
- direct changes to `map.db`, task JSON, task graph, or event log;
- authority or policy decisions.

## Escalation Triggers

Escalate back to a core agent when:

- helper is uncertain;
- output changes scope;
- output touches approval gates, task claims, cost governance, security, or
  policy;
- helper finds conflicting canonical sources;
- helper suggests broad refactor;
- output would be treated as final by another worker.

## Lane-Specific Guardrails

`repo_scan`:

- read only;
- do not use as proof that unlisted files are irrelevant;
- core agent decides final context packet.

`json_schema_check`:

- fixtures are allowed;
- no canonical writes;
- report exact field/path failures.

`event_digest`:

- use bounded event windows;
- distinguish hcom chatter from durable events;
- do not infer decisions not present in durable state.

`validator_log_summary`:

- preserve command and exit code;
- name exact failing validator;
- do not patch.

`markdown_cleanup`:

- no semantic changes;
- no policy changes;
- core owner reviews every edit.

`acceptance_criteria_draft`:

- criteria must be binary and file-grounded;
- cannot approve its own criteria.

## Relationship To TASK-153 Tiering

`gap_score` and `task_tier` determine whether a lane is allowed. A low score
can allow local draft work; a high score can still allow narrow inspection,
but final ownership remains core. `local_lane=null` is valid and should be
used when helper work would add coordination cost without reducing risk.
