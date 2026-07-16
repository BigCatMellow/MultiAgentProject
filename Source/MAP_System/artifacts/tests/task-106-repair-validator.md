# TASK-106 Repair Validator Test Notes

Task: TASK-106
Owner: codex-lab-dino
Date: 2026-07-03

## Scope

Added a focused Self-Repair System validator and tests.

## Implemented

- `MAP_System/scripts/validate_repair_artifacts.py`
  - Verifies both Self-Repair templates exist.
  - Checks required fields and headings from the approved TASK-105 contract.
  - Scans MAP-level and project-level repair/health artifact folders.
  - Rejects unknown repair artifact prefixes.
  - Rejects final/applied/completed repair and health artifacts that still
    contain raw placeholder tokens.
- `MAP_System/tests/test_validate_repair_artifacts.py`
  - Covers a clean temporary Self-Repair template set.
  - Covers a missing required template fragment.
  - Covers an applied repair record with unresolved placeholders.
- `MAP_System/scripts/run_tests.sh`
  - Runs the validator and focused test as part of the MAP suite.

## Verification

- `python3 MAP_System/scripts/validate_repair_artifacts.py` - PASS.
- `python3 MAP_System/tests/test_validate_repair_artifacts.py` - PASS.
- `python3 -m py_compile MAP_System/scripts/validate_repair_artifacts.py MAP_System/tests/test_validate_repair_artifacts.py` - PASS.

## Notes

This validator is structural. It does not judge whether a proposed repair is
the right policy choice; it catches missing templates and malformed final
repair/health artifacts before they become durable process memory.
