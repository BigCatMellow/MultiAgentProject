<!-- hpom: file: shared/improvement-backlog.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-06-29 -->
<!-- hpom: verified_against: Phase 2 sprint close 2026-06-29 -->
<!-- hpom: confidence: MEDIUM -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Improvement Backlog

This file tracks MAP improvements that are known but not yet safe to apply
silently. Use it for issues found by audits, reviews, or scout passes that need
intentional follow-up.

## High Priority

### Add operator-request worker-fit intake and ownership protocol

Status: first pass complete — TASK-065 added `scripts/intake_request.py` and
`shared/approval-calibration.md`; still needs habit adoption and possible UI
integration.

The Command Center Lab exposed a core MAP bypass: when the operator gives an
ad-hoc request in hcom or chat, multiple core agents may start doing the same
work before the request becomes a claimed task, review assignment, or explicit
handoff. The deeper failure is that the request is not first routed by worker
fit across Codex, Claude, local models, visible helpers, or the human operator.

Impact:

- Agents can duplicate work instead of using MAP ownership and review roles.
- Work can go to the most eager or available agent instead of the worker best
  suited to the task shape.
- The operator has to coordinate collisions manually, defeating the purpose of
  the task system.
- Review history becomes harder to reconstruct because some work happens as
  live chat response rather than under a task owner or run record.

Recommended next action:

- Add an intake rule for operator requests: classify the request, choose the
  best worker type from `shared/agent-capability-matrix.md`, assign one
  accountable owner, and announce `worker_fit`, `reason`, `owner`, `reviewer`,
  `support`, or `standing_down` through hcom before substantive work begins.
- For implementation or repository-global work, require either a task claim or
  a session-scoped ownership record before file edits or Git operations.
- Make the non-owner switch to review/support mode unless explicitly handed the
  task.
- Use local models only for bounded draft/check/summary outputs with a core
  owner reviewing the result before MAP state changes.
- Keep the first implementation lightweight: documented protocol plus a small
  script/check is preferable to broad automation.

### Add Git operation coordination lock

Status: first pass complete — TASK-065 added `scripts/git_operation_lock.py`;
still needs adoption before actual commit/push/sync operations.

The Command Center Lab exposed a coordination gap: two core agents can try to
commit or push the same working tree at the same time after an operator says
"push the git."

Impact:

- Agents can race on staging, commits, remote pushes, and status interpretation.
- One agent can create a local commit while another pushes a different local
  state or reports a stale remote state.
- Operator-facing Monitor output becomes confusing because multiple agents are
  acting on the same global repository resource.

Recommended next action:

- Add a MAP Git operation owner/lock for commit, push, pull, fetch-with-ref
  update, release baseline, and other repository-global operations.
- Require the active Git owner to announce the operation through hcom before
  staging or pushing.
- Require other agents to stand down or explicitly hand off before attempting
  overlapping Git operations.
- Prefer a small script-level guard before adding database triggers or broader
  automation.

### Enforce READY state metadata gate

Status: **DONE** — completed TASK-035 (2026-06-29)

`scripts/promote_task.py` now validates 8 HPOM JSON fields and SQLite fields
before setting status to READY. CONFLICT tasks are blocked. See
`artifacts/reviews/` for gate test coverage.

### Define Architect/Shaper role

Status: **DONE** — completed TASK-036/TASK-037 batch (2026-06-29)

`shared/agent-capability-matrix.md` defines helper vs. core vs. local model
roles. `scripts/promote_task.py` is the shaping gate. No agent claims an
unready task.

### Clean up stale `langgraph/` references

Status: open

The live orchestration directory is `graph/`, but historical task and artifact
records still mention `langgraph/`.

Impact:

- Agents can waste time following dead paths.
- Historical artifacts are harder to distinguish from current instructions.

Recommended next action:

- Leave historical records intact when they are clearly provenance.
- Update live docs and any task records that are still treated as current input.
- Add a short note to old review/test artifacts only if they are likely to be
  reused as current instructions.

## Medium Priority

### Add atomic task ID allocation

Status: **DONE** — completed TASK-065

`scripts/map_task.py create --task-id auto` now reserves the next `TASK-NNN`
inside a SQLite write transaction and exports file mirrors immediately.
Agents should use this instead of manually choosing the next ID during active
multi-agent sessions.

### Add emergence stale/lifecycle reporting

Status: first pass complete — TASK-065 added `map_emergence.py stale`; TASK-075
handled root emergence record cleanup.

The stale report flags placeholder content, dangling promotion references,
and records tied to closed tasks but still left open.

### Add event log validation/reporting

Status: first pass complete — TASK-065 added `scripts/validate_events.py`.

The validator parses JSONL, reports legacy `timestamp`/`agent` fields, aliases
legacy event types, and can run in strict mode for new logs.

### Add agent availability reconciliation

Status: first pass complete — TASK-065 added `scripts/reconcile_agents.py`.

The report distinguishes durable known-agent status from live hcom sessions.

### Add live hcom and MAP state wiring to CommandCenterUI

Status: open — follow-up from TASK-055

TASK-055 delivered the first static Studio-style Command Center UI prototype.
Live integration was intentionally left out of scope.

Recommended next action:

- Create a new task for read-only `hcom`/MAP status and event loading into the
  UI.
- Add operator-gated send and approval actions only after read-only state is
  working.
- Keep file writes, external pushes, and process control behind explicit
  approval paths.

### Define handler execution safety policy

Status: open

`scripts/agent_loop.py` executes handler commands through the shell after
`{task_id}` substitution. This is flexible but should remain trusted operator
configuration only.

Impact:

- Unsafe if handler strings are built from untrusted input.
- Easy for future agents to copy into a less trusted context.

Recommended next action:

- Either document the trusted-handler boundary directly in `AGENTS.md`, or add
  an argv-based handler mode while preserving the current shell mode for
  compatibility.

### Decide first real general MAP workflow target

Status: open

`shared/unresolved-questions.md` still asks whether the first real workflow
target should be writing, software, research, or general project management.

Impact:

- MAP can keep accumulating infrastructure without a concrete proving workflow.

Recommended next action:

- Pick one target and create the next task sequence around it.

### Fix --no-auto-commits in aider_wrapper.py FORBIDDEN_AIDER_FLAGS

Status: open — tracked as TASK-050

`FORBIDDEN_AIDER_FLAGS` incorrectly blocks `--no-auto-commits`, which is a
safety flag. Only `--auto-commits` should be blocked. See TASK-049 review
finding at `artifacts/reviews/task049-aider-wrapper-review.md`.

### Clean up OPTIONAL findings from local_runner.py (TASK-048 review)

Status: open — tracked as TASK-051

Two cosmetic items: unreachable `if output_path is None` guard (line 137,
`--output` is `required=True` in argparse) and try/except ModuleNotFoundError
import pattern. See `artifacts/reviews/task048-local-runner-review.md`.

## Maintenance Priority

### Add recurring brain compaction

Status: open

The active MAP brain should not grow by permanently appending every completed
task narrative to current files.

Impact:

- Active docs can become expensive to read.
- Agents may confuse historical detail with current truth.
- Decisions and status files can become transcripts instead of operating memory.

Recommended next action:

- Follow `notes/brain-compaction-guide.md` after each batch of roughly 10
  completed or approved tasks.

### Keep current-state fresh

Status: ongoing

`shared/current-state.md` should be updated whenever the runnable system changes.

Impact:

- If stale, agents may trust obsolete status over executable reality.

Recommended next action:

- Include current-state updates in any task that changes runner, task claiming,
  approval gates, helper policy, or validation behavior.
