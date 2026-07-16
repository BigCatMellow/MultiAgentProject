# TASK-121 MAP Folder Cleanup Report

task_id: TASK-121
owner: codex-lab-dino
date: 2026-07-03

## Backup

Fresh backup was created before edits:

- `Projects/Backups/MAP_System-backup-2026-07-03T120105Z`
- Verification: `diff -qr MAP_System Projects/Backups/MAP_System-backup-2026-07-03T120105Z` returned no differences.
- Size check: live `MAP_System` and backup both reported `87M`.

## Audit Scope

Checked:

- top-level `MAP_System/` files and folders;
- major folder README coverage;
- empty directories;
- ignored runtime/cache directories;
- artifact subfolder routing;
- task output-path registration for this cleanup.

## Findings

### Applied Non-Destructive Cleanup

- Added missing artifact subfolder indexes:
  - `artifacts/planning/README.md`
  - `artifacts/reports/README.md`
  - `artifacts/releases/README.md`
  - `artifacts/reviews/README.md`
  - `artifacts/tests/README.md`
  - `artifacts/command-center-ui/README.md`
- Created the documented-but-missing `artifacts/planning/` folder with a README.
- Updated `artifacts/README.md` to list `releases/`, `reports/`, and
  `command-center-ui/`, which already existed or was actively used but was
  not described there.
- Corrected TASK-121's initial output path from a new `artifacts/structure/`
  category to the existing `artifacts/reports/` category. A structure report
  is a report, not a new artifact class.

### No-Op / Preserved Layout

- No folder moves or deletes were applied.
- `MAP_System/` already matches the major layout in
  `notes/brain-organization-guide.md`: `shared/`, `tasks/`, `workflow/`,
  `notes/`, `templates/`, `artifacts/`, `handoffs/`, `inbox/`, `events/`,
  `archive/`, plus the newly built `repairs/` and `research/` systems.
- `.venv/`, `.locks/`, `map.db`, and `__pycache__/` directories are already
  ignored by the root `.gitignore`; they are runtime/cache state, not cleanup
  targets for this task.
- `Projects/Backups/` is ignored and should stay outside MAP active context
  unless a task specifically needs backup provenance.

### Structural Proposals

None. I found no evidence that a canonical folder should be moved, renamed, or
deleted. Any such change would be STRUCTURAL under `SELF_REPAIR_SYSTEM.md` and
should be proposed separately, not applied during this cleanup.

## Verification Plan

- `MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py`
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py`
- `MAP_System/scripts/run_tests.sh`
