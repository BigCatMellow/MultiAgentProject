# TASK-045 Exporter HPOM Field Preservation Test

Date: 2026-06-29
Owner: codex-live

## Scope

Verified that `export_to_files.py` preserves existing task JSON fields that are not represented in the SQLite schema.

## Commands

```bash
python3 MAP_System/tests/test_exporter_hpom_fields.py
python3 -m py_compile MAP_System/migration/export_to_files.py MAP_System/tests/test_exporter_hpom_fields.py
MAP_System/scripts/run_tests.sh
```

## Results

- `objective`, `reviewer_role`, and `risk` survived a SQLite-to-file export round trip.
- Canonical SQLite fields still overwrote stale task file values such as `title` and `status`.
- Existing `input_paths` were preserved.
- Full MAP test wrapper passed with `SUMMARY pass=7 fail=0 total=7`.
