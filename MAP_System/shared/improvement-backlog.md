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

### Add emergence stale/lifecycle reporting

Status: first pass complete — TASK-065 added `map_emergence.py stale`; TASK-075
handled root emergence record cleanup.

The stale report flags placeholder content, dangling promotion references,
and records tied to closed tasks but still left open.

### Add event log validation/reporting

Status: baseline gate active — TASK-065 added `scripts/validate_events.py`;
TASK-142 added `events/warning_baseline.json` and `--fail-on-new` wiring.

The validator parses JSONL, reports legacy `timestamp`/`agent` fields, aliases
legacy event types, and distinguishes accepted historical warnings from new
warning-worthy event lines. `scripts/run_tests.sh` runs `--fail-on-new`, so new
event-shape warnings should fail the suite instead of hiding inside the legacy
33-warning baseline.

### Add agent availability reconciliation

Status: first pass complete — TASK-065 added `scripts/reconcile_agents.py`.

The report distinguishes durable known-agent status from live hcom sessions.

### Add live hcom and MAP state wiring to CommandCenterUI

Status: **DONE** in substance — live hcom chat/presence/approvals wired by TASK-087/088/093/094; MAP runtime health card by TASK-182. Remaining ideas belong to new tasks, not this item.

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

### Add optional `delete_thread()` coverage to `MapSqliteSaver`

Status: open — found by TASK-145 Research Summary, recorded during TASK-144

The current LangGraph checkpointer usage aligns with official 1.x practice,
but `db/checkpointer.py` does not implement a `delete_thread()` override. MAP
does not call this method today, so this is a latent completeness gap rather
than a live bug.

Recommended next action:

- Add a small task if MAP begins managing LangGraph thread lifecycle directly,
  or if a future checkpointer validator expects the full saver method surface.
  Keep it low priority until then.

## Maintenance Priority

### Add recurring brain compaction

Status: first run complete — TASK-193 (2026-07-14) produced `archive/compactions/compaction-2026-07-14-tasks-147-192.md`. Item stays open for the RECURRING part: next compaction due per the guide's 10-task trigger (~TASK-203) or next phase end.

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

### Make output_paths registration explicit for cross-linked files

Status: applied — fix identified in RETRO-0001 (TASK-118) and applied the
same task to `notes/task-authoring-guide.md`

Across the TASK-103 through TASK-117 gap-review build sequence, the
requirement that *any* file touched by an edit — including a one-line
cross-link backlink added in another system's doc — must be registered in
a task's `output_paths` before submission was not obvious from
`notes/task-authoring-guide.md` alone. It recurred as a near-miss across
TASK-111, TASK-112, TASK-115, and TASK-117, each time caught by a
reviewer's proactive heads-up before submission rather than by the
authoring guide itself.

Impact:

- Extra back-and-forth between task owner and reviewer on every
  cross-linking task.
- Risk that a smaller/rushed task skips this check entirely and reaches
  review with an undeclared output path.

Recommended next action:

- Add an explicit line to `notes/task-authoring-guide.md`'s Output Paths
  section stating that any file touched by an Edit/Write call — including
  a one-line cross-link backlink in another system's file — counts as an
  output path, not just the task's named primary deliverables.

### RnS watcher small follow-ups from TASK-187 review

Status: open (OPTIONAL/LOW findings from `artifacts/reviews/task187-review-toku.md`, 2026-07-14)

- `state["terminal_suppressed"]` map in `limit_watcher.py` grows forever —
  entries are never pruned when a terminal agent is deleted from durable
  status or returns via `--back`. Cosmetic until the map is large; fold into
  the next watcher task.
- Dry-run output does not exercise/show the active-session fallback branch
  (`hcom r` "still active" → `hcom send`), so a dry-run reviewer can't see it.
  Add a dry-run print for the fallback decision path.
- LOW risk: the fallback trigger regexes hcom's "is still active" error text;
  an hcom upgrade that rewords the error silently disables the fallback.
  Mitigation habit: after `hcom update`, re-run
  `strings ~/.local/bin/hcom | grep "still active"` (toku's verification
  trick) or add a health-check line to `local_assistant_health.py`-style
  checks for it.

## Completed (details in archive/compactions/compaction-2026-07-14-tasks-147-192.md and task records)

- Add task-state mirror reconciliation gate — completed TASK-143 (2026-07-04)
- Enforce READY state metadata gate — completed TASK-035 (2026-06-29)
- Define Architect/Shaper role — completed TASK-036/TASK-037 batch (2026-06-29)
- Add atomic task ID allocation — completed TASK-065
- Fix --no-auto-commits in aider_wrapper.py FORBIDDEN_AIDER_FLAGS — completed TASK-050
- Clean up OPTIONAL findings from local_runner.py (TASK-048 review) — completed TASK-051
- Add atomic ID allocation for Self-Repair records — emergence allocation fixed by REPAIR-0005 (TASK-141);
