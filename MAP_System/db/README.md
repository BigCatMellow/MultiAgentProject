# db/

This directory contains the SQLite database module for task claiming.

## Files

- `claims.py` — atomic task claim, heartbeat, submit, and no-self-review helpers
- `checkpointer.py` — LangGraph SQLite checkpointer (future runtime)
- `map.db` — **zero-byte stub; not the canonical database**

## Canonical Database Location

The live database is at `MAP_System/map.db` (one level up).
All scripts default to `MAP_System/map.db`. The `db/map.db` file is a
placeholder left from an earlier layout and is not used.

## Migration

SQL migrations live in `db/migration/` and are applied by `migration/schema.sql`
and `migration/seed_from_files.py`.
