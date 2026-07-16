<!-- hpom: file: shared/agent-capability-matrix.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: MAP_System audit 2026-06-29 -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Agent Capability Matrix

Status: working HPOM routing reference
Owner: command-center
Related: `shared/hpom.md`, `notes/local-model-helper-guide.md`

## Rule

Assign work by fit, not by availability.

If a worker cannot produce a reliable output for the task shape, do not use it
just to keep it busy.

## Core Agents

| Worker | Best At | Good Outputs | Avoid | Default Authority |
|---|---|---|---|---|
| Codex | Code edits, scripts, validators, SQLite, CLI tools, tests, precise file changes | implementation, test artifact, bug fix, task shaping with concrete files | approving its own implementation, vague product decisions, broad unsupervised refactors | owns implementation |
| Claude | Review, architecture critique, synthesis, task shaping, prose-heavy documentation, risk analysis | review findings, architecture note, acceptance criteria, operator summary | approving its own deliverable, hidden implementation without task ownership | owns review/planning |

## Standby / Manual Agents

| Worker | Best At | Use When | Avoid | Current Status |
|---|---|---|---|---|
| Gemini | alternate brainstorming, broad summaries, second-pass ideation when manually prompted | operator explicitly activates it for bounded support | relying on passive hcom awareness or final authority | standby/manual |
| Antigravity | GUI/IDE-style exploratory support if token budget and CLI behavior are healthy | operator explicitly activates it and the task benefits from visual/workbench context | routing dependency, hidden background work, token-heavy routine checks | standby/out of tokens |

## Local Models

| Worker | Best At | Good Outputs | Avoid | Authority |
|---|---|---|---|---|
| `llama3.2:3b` | orientation, event digest, current-state summary | summary, open-question extraction, task overview | final decisions, complex architecture, code edits | draft-only |
| `llama3.2:1b` | tiny fast classification | one-line summary, task/note/review label | nuance, long docs, code | draft-only |
| `qwen2.5-coder:3b` | JSON, schemas, validators, small Python/SQLite helpers | checklist result, suggested JSON, small diff idea | final architecture, broad refactor, ambiguous intent | draft-only |
| `qwen2.5-coder:1.5b` | fast syntax/path checks | quick PASS/FAIL, typo or key check | deep reasoning, final code review | draft-only |
| `gemma3:4b` | acceptance criteria, markdown cleanup, structured writing | draft criteria, doc cleanup suggestion, review draft | final approval, policy decisions | draft-only |

## Tools

| Tool | Best At | Preconditions | Avoid |
|---|---|---|---|
| Aider | narrow supervised edits using local coding model | Git baseline understood, explicit task id, explicit output paths, helper note path | broad cleanup, unclear scope, final authority |
| hcom | visible agent orchestration and messaging | use `--terminal wezterm-tab` for spawned agents/helpers unless explicitly told otherwise | treating messages as durable memory without file records |
| LangGraph runner | next-route recommendation and approval interrupts | task graph valid, file/SQLite state synced | canonical memory or autonomous helper spawning |

## Assignment Checklist

Use a local assistant when all are true:

- the task can be reduced to summary, classification, checklist, draft, or
  diff suggestion;
- the output can be reviewed by Codex or Claude before changing MAP state;
- input paths are bounded;
- no human intent, approval, or architecture decision is required.

Use a temporary hcom helper when all are true:

- the scope is bounded;
- parallelism saves real time;
- a core owner will integrate or reject the result;
- a durable helper note exists;
- the session is visible or command-center-reachable.

Use a core agent directly when:

- implementation changes MAP behavior;
- the task changes task state, claims, approval gates, or helper policy;
- the work requires judgment about system design;
- the result will be treated as final after independent review.

Ask command-center when:

- the task intent cannot be made pass/fail;
- HPOM/MAP boundaries are changing;
- helper use would require hidden or expensive subscription work;
- a preference tradeoff matters more than a technical check.

## Observed Health

- Active hcom sessions as of 2026-06-29 restart: `codex-live`, `claude-mako`.
- Durable `agents/status.json` still contains historical agent ids; use live
  `hcom list` before assigning real-time work.
- Local model availability has not yet been checked in this session. Run
  `TASK-036` before depending on Ollama/Aider.
