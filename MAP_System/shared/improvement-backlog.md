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
