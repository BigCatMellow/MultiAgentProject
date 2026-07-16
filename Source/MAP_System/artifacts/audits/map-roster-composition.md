# MAP Roster Composition Audit (TASK-157, Wave 9)

Status: draft-active
Owner: command-center
Built by: TASK-157

## Purpose

This audit compares two-tier and three-tier MAP routing without registering
new agents. It uses current observations from the live session and existing
MAP specs to decide what should be tested next.

## Current Observations

Observed in this session:

- core agents can own implementation, validation, task submission, and review
  integration;
- visible helper/reviewer tabs are useful for bounded independent review;
- one Claude lab agent hit a script-execution/tool-safety outage while still
  able to perform simple reads and hcom communication;
- local/Ollama lanes were not needed for the completed architecture/spec tasks;
- runner reports helper capacity separately from ready/in-progress tasks.

This is operational evidence, not a controlled experiment.

## Two-Tier Model

Tiers:

1. Core agents: Codex/Claude-style agents with repo write and task ownership.
2. Helpers/local draft lane: all bounded review, summary, and local work.

Advantages:

- simpler policy and fewer routing decisions;
- less chance of a helper/local distinction being misunderstood;
- easier operator mental model;
- lower overhead for small work queues.

Risks:

- visible helpers and local assistants have very different capabilities but
  would share one conceptual tier;
- local no-network/no-shell constraints can be obscured;
- high-quality visible reviewers may be underused if grouped with draft-only
  local output;
- cost/governance decisions become less precise.

Best fit:

- small teams;
- mostly core-agent work;
- occasional read-only helper review;
- no substantial local model automation.

## Three-Tier Model

Tiers:

1. Core agents: task owners, integrators, final submitters.
2. Visible helpers/reviewers: bounded independent review, source inspection,
   draft recommendations, no final approval.
3. Local assistants/Ollama/Aider lanes: draft-only, no shell/network/canonical
   authority, narrow named-file or summary tasks.

Advantages:

- matches `AGENT_PERMISSION_LEVELS.md`;
- preserves the useful difference between visible human-monitorable helper
  tabs and draft-only local tools;
- supports cost governance by routing cheap local drafts separately;
- allows capability whitelist tests to be concrete.

Risks:

- more routing metadata is required;
- operator may see more categories in mission-control;
- bad pre-dispatch classification can overuse local lanes or over-block
  helpful visible reviewers;
- local helper output quality must be measured, not assumed.

Best fit:

- sustained MAP system work;
- multiple independent reviews;
- expensive cloud model budget pressure;
- clear local helper lanes like repo scans, schema checks, or digest drafts.

## Agent Count Considerations

Core agents:

- Minimum useful count: 2, so one can implement and another can review or
  continue unrelated work.
- Practical live count: 2-4 active core agents before hcom/operator overhead
  starts to dominate.

Visible helpers:

- Useful count: 1-4 bounded helpers, matching current helper capacity.
- Best uses: independent review, focused red-team notes, source inventory,
  validator log summaries.

Local assistants:

- Count should be capability-driven, not roster-driven.
- Add only when a named local lane repeatedly saves core time without causing
  rework.

Do not register new agents based on this audit. Registration should follow
actual measured demand and health checks.

## Recommendation

Keep the three-tier model as the design target because it matches current
permission files and supports pre-dispatch governance. Operate it conservatively:

- core agents own integration and all canonical mutation;
- visible helpers perform bounded review/red-team work in visible tabs;
- local assistants remain draft-only until task-tier and capability whitelist
  tests show reliable value.

The next evidence needed is not a larger roster; it is measurement of helper
usefulness, local-lane rework rate, and operator attention cost.
