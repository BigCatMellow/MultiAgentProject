# synthesis/ (ProjectUpdater)

Per `MAP_System/PROJECT_BOOTSTRAPPING_SYSTEM.md`'s Emergence capacity
requirement (DEC-026), this folder exists so a project-level synthesis
note has somewhere to live if one is captured directly here.

In practice, `MAP_System/scripts/map_emergence.py synthesis --project
ProjectUpdater ...` (the standard CLI, with ID allocation, index
rebuilding, and stale-checking) always writes to
`MAP_System/emergence/synthesis/`, tagged `Project: ProjectUpdater` in
the record's metadata — it does not currently route to a project-specific
folder. No synthesis notes have been written for ProjectUpdater yet.

This folder stays as the place a future project-local, non-CLI synthesis
note could go, and as the honest empty starting point the bootstrap
wizard requires. See `MAP_System/emergence/README.md` for the full system.
