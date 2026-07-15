# insights/ (ProjectUpdater)

Per `MAP_System/PROJECT_BOOTSTRAPPING_SYSTEM.md`'s Emergence capacity
requirement (DEC-026), this folder exists so a project-level insight has
somewhere to live if one is captured directly here.

In practice, `MAP_System/scripts/map_emergence.py insight --project
ProjectUpdater ...` (the standard CLI, with ID allocation, index
rebuilding, and stale-checking) always writes to
`MAP_System/emergence/insights/`, tagged `Project: ProjectUpdater` in the
record's metadata — it does not currently route to a project-specific
folder. All of ProjectUpdater's real insights (INS-0011, INS-0012,
INS-0013) live there, not in this folder.

This folder stays as the place a future project-local, non-CLI insight
could go, and as the honest empty starting point the bootstrap wizard
requires. See `MAP_System/emergence/README.md` for the full system.
