# Project Map

This workspace deliberately separates the reusable multi-agent system from the
active project that uses it.

## Root

- `README.md` - human-facing overview.
- `AGENTS.md` - root instructions all AI agents should read. Includes a routing table: what question → which folder.
- `CLAUDE.md` - Claude Code pointer into the same root workflow.
- `TASKS.md` - explains that active task boards live in project directories.
- `Guidelines/` - **universal** AI collaboration protocols (communication rules, laziness ladder, context pruning, prompt skeleton, schema pin). Apply to any project in this workspace, not MAP-specific.
- `start-all-agents.sh` - launches the local agent set through `hcom`.
- `launchers/` - desktop files for terminal and command-center launchers.
- `archive/` - inactive scratch or retired files.

## Reusable MAP System

- `MAP_System/README.md` - system overview.
- `MAP_System/AGENTS.md` - operating rules for MAP system work.
- `MAP_System/shared/` - durable project facts, requirements, decisions, and
  unresolved questions.
- `MAP_System/emergence/` - creative discovery system for insights, synthesis,
  idea cards, experiments, and promotion records before work becomes HPOM tasks.
- `MAP_System/tasks/` - task records.
- `MAP_System/workflow/` - workflow definitions, runtime policy, approval rules,
  and the task graph.
- `MAP_System/scripts/` - CLI helpers, validation, reconciliation, and tests.
- `MAP_System/db/` and `MAP_System/migration/` - SQLite-backed state support.
- `MAP_System/artifacts/` - completed work products, reviews, planning, and
  test notes.
- `MAP_System/events/events.jsonl` - append-only collaboration log.

## Pathwell Project

- `Projects/Pathwell/README.md` - Pathwell overview.
- `Projects/Pathwell/AGENTS.md` - Pathwell-specific agent rules.
- `Projects/Pathwell/Story_Files/` - canon, voice, tone, and story reference files.
- `Projects/Pathwell/Chapters/` - active chapter text and editorial context.
- `Projects/Pathwell/insights/`, `synthesis/`, `ideas/`, and `experiments/` -
  Pathwell-specific emergence artifacts.
- `Projects/Pathwell/Chapters (copy)/` - duplicate chapter material; inspect before
  using as source of truth.
- `Projects/Pathwell/MAP_System/` - project-local MAP state for Pathwell tasks.

## Backups

- `Projects/Backups/MAP_System-backup-2026-06-27/` - reusable MAP backup before
  separating the Pathwell run from the top-level MAP engine.

## Context Hygiene

Default to reading the smallest relevant set of files:

1. Root `AGENTS.md`
2. Relevant project `AGENTS.md`
3. Relevant `shared/` files
4. Relevant task JSON
5. Directly related artifacts, handoffs, or source files

Avoid loading `.venv/`, `.locks/`, `logs/`, `exports/`, `snapshots/`,
database binaries, or archived files unless they are explicitly relevant.
