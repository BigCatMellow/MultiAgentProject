# MAP Runtime Derived State

This directory is for local, rebuildable runtime artifacts.

`session_replay.sqlite` is produced by:

```bash
python3 MAP_System/scripts/session_replay.py build
```

It is a disposable read model built from canonical MAP sources such as
`events/events.jsonl`, `map.db`, and `tasks/*.json`. It is safe to delete and
rebuild. It must not become a source of truth, and mission-control surfaces
should treat stale or drifted replay data as a warning condition.
