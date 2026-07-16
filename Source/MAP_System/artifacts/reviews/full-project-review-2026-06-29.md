# Full Project Review - 2026-06-29

Reviewer: codex-live
Scope: root workspace organization, reusable `MAP_System/`, active
`Projects/Pathwell/`, task and review state, validation, naming consistency,
and near-term readiness.

## Verdict

The reusable MAP system is functionally healthy and meets its current
coordination goals. Core gates, tests, review validation, SQLite task state,
local assistant health checks, and shared-state validation pass.

The full workspace is not yet "complete" because the active Pathwell project
still has open/submitted/in-progress tasks and an unresolved chapter
source-of-truth mismatch. Before manuscript work continues at scale, Pathwell
needs a specific reconciliation task for chapter directories and task ownership.

## Evidence

- `MAP_System/scripts/run_tests.sh`
  - Result: `SUMMARY pass=12 fail=0 total=12`
- `python3 MAP_System/scripts/validate_task_graph.py`
  - Result: pass
- `python3 MAP_System/scripts/validate_shared_state.py`
  - Result: 16 shared files checked, 0 failures, 0 warnings
- `python3 MAP_System/scripts/validate_decisions.py`
  - Result: 11 decisions checked, 0 failures
- `python3 MAP_System/scripts/local_assistant_health.py --json`
  - Result: status ok; Ollama reachable; required models available; Aider
    available as `aider 0.86.2`
- `cd Projects/Pathwell && python3 MAP_System/scripts/validate_task_graph.py`
  - Result: pass
- `python3 MAP_System/scripts/map_metrics.py --json`
  - Result: conflict count 0, review queue size 0, stale shared file count 0

## Current Task State

Reusable MAP system:

- `DONE`: 20
- `RELEASED`: 29
- `IN_PROGRESS`: 1 (`TASK-050`, claimed by `codex-live` before this audit)
- `READY`: 1 (`TASK-051`)
- No submitted review queue and no active conflict count.

Pathwell project:

- Approved tasks: `TASK-001` through `TASK-005`
- In progress: `TASK-006`, `TASK-011`
- Submitted: `TASK-007`, `TASK-009`, `TASK-010`
- Ready: `TASK-008`

## Findings

### REQUIRED: Resolve Pathwell Chapter Source Of Truth

`Projects/Pathwell/Chapters/` and `Projects/Pathwell/Chapters (copy)/` both
exist and are not equivalent. The duplicate copy contains `Chapter_13.txt`; the
active `Chapters/` directory does not. File counts observed:

- `Projects/Pathwell/Chapters/`: 13 files
- `Projects/Pathwell/Chapters (copy)/`: 14 files
- Difference: `Chapter_13.txt` exists only in `Chapters (copy)`

`docs/project-map.md` already warns that `Chapters (copy)/` is duplicate
material that must be inspected before using it as source of truth. This is the
highest-risk workspace issue because multiple Pathwell tasks are currently
working on extraction, normalization, and generated sequence review.

Required next action: create and complete a Pathwell reconciliation task before
new manuscript transformation work proceeds. The task should decide whether
`Chapter_13.txt` belongs in active `Chapters/`, whether `Chapters (copy)/`
should be archived, and which submitted tasks need re-review after that
decision.

### REQUIRED: Checkpoint Or Clean The Dirty Worktree

`MAP_System/scripts/map-git status --short` shows a very large dirty state:
deleted legacy `Pathwell/` files, new `Projects/Pathwell/`, new MAP scripts,
new task files, new artifacts, renamed hyphenated docs, generated cache files,
and current code/test edits.

This appears consistent with a major repository reorganization, but it is too
large to treat as incidental. Until it is committed, backed up, or explicitly
partitioned, it is a recovery and review risk.

Required next action: make a deliberate checkpoint plan:

- group reusable MAP changes;
- group Pathwell relocation/content changes;
- exclude generated caches and transient files;
- confirm no active task output is lost before commit or archive.

### REQUIRED: Finish Open MAP Cleanup Tasks

`TASK-050` was claimed before the full-project-review request arrived. The code
change and tests are already passing, but it has not been submitted. `TASK-051`
remains ready.

Required next action: after this audit, submit `TASK-050` for independent
review and then let the command center decide whether to claim `TASK-051` or
prioritize the Pathwell reconciliation task.

### REQUIRED: Remove Or Explain Zero-Byte Duplicate Database

The canonical database is `MAP_System/map.db`:

- size: 4.4 MB
- `tasks`: 51
- `events`: 156
- `decisions`: 11

`MAP_System/db/map.db` is a zero-byte file with no tables. Because
`MAP_System/db/` also contains database support code, this stray file can
confuse future agents or scripts.

Required next action: remove it if it is accidental, or document why it exists
if it is intentionally reserved.

### RECOMMENDED: Refresh MAP README Current Status

`MAP_System/README.md` still says the next hardening issue is preventing
incomplete metadata from entering `READY`. That work is now implemented and
released through the HPOM gates. The current status should instead point to
open cleanup tasks, local assistant wrapper status, and the Pathwell audit
dependency if relevant.

### RECOMMENDED: Refresh Pathwell README Source Pointers

`Projects/Pathwell/README.md` points to
`MAP_System/archive/root-map-pathwell-run-2026-06-27/` as a start-here item.
That pointer may be historical rather than active. The README should align with
`docs/project-map.md`: active story source is `Story_Files/` and `Chapters/`,
while duplicate chapter material requires inspection before use.

### RECOMMENDED: Clean Or Ignore Generated Files

The workspace contains generated/transient files such as:

- `MAP_System/.aider.chat.history.md`
- `MAP_System/.aider.input.history`
- `MAP_System/.aider.tags.cache.v4/`
- Python `__pycache__/` directories

These should be ignored, cleaned, or explicitly kept out of release commits.

### RECOMMENDED: Retire Live-Doc Legacy References

Some historical `langgraph/` references remain in live or historical docs. The
current tree uses `MAP_System/graph/`. Keep historical references only where
they describe archived context; update active operating docs to avoid ambiguity.

## Organization And Naming Assessment

The top-level structure is coherent:

- `MAP_System/` for reusable coordination system work
- `Projects/Pathwell/` for the active story project
- `Projects/Backups/` for dated backups
- `Guidelines/` for reference material
- `docs/` for workspace navigation
- `archive/` for inactive scratch or retired files

Naming is mostly consistent:

- Markdown shared docs are mostly hyphenated.
- Scripts are snake_case Python or executable CLI names.
- Task IDs use `TASK-NNN`.
- Decision IDs use `DEC-NNN`.

Remaining naming/organization concerns are specific and fixable:

- Pathwell still has underscore-style project-local docs because that MAP copy
  preserves older conventions.
- `Chapters (copy)/` is an ambiguous active-looking directory name.
- `MAP_System/db/map.db` looks like a canonical database location but is not.
- Some old deleted paths and new replacement paths still coexist only as a
  dirty Git state until committed.

## Goals Check

Reusable MAP goals:

- Durable file-based multi-agent coordination: met.
- Task ownership and review gates: met.
- SQLite-backed claims and graph validation: met.
- Shared-state and decision validation: met.
- Local assistant runner and Aider wrapper: met for released work, with
  `TASK-050` pending submission.

Pathwell project goals:

- Project-local MAP task system: operational.
- Story source material organized under `Story_Files/` and chapters: partially
  met.
- Manuscript transformation and chapter review goals: in progress, not complete.
- Current blocker: chapter source-of-truth mismatch.

## Recommended Next Steps

1. Submit `TASK-050` for independent review.
2. Create or promote a Pathwell task to reconcile `Chapters/` versus
   `Chapters (copy)/`, including `Chapter_13.txt`.
3. Pause new Pathwell manuscript transformation claims until the chapter source
   decision is recorded.
4. Decide whether `TASK-051` should run before or after Pathwell reconciliation.
5. Remove or document `MAP_System/db/map.db`.
6. Refresh `MAP_System/README.md` and `Projects/Pathwell/README.md`.
7. Create a Git checkpoint plan that separates MAP system changes, Pathwell
   relocation/content changes, and generated files.

## Bottom Line

The MAP system is ready for continued use. The workspace as a whole should not
be declared complete until Pathwell's chapter source of truth is reconciled and
the current large uncommitted reorganization is checkpointed.
