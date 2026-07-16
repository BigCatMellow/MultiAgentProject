# TASK-104 Research Validator Test Notes

Task: TASK-104
Owner: codex-lab-dino
Date: 2026-07-03

## Scope

Added a focused Research System validator and tests.

## Implemented

- `MAP_System/scripts/validate_research_artifacts.py`
  - Verifies all six Research System templates exist.
  - Checks required headings/fields from the approved TASK-103 contract.
  - Scans MAP-level and project-level research artifact folders.
  - Rejects unknown research artifact prefixes.
  - Rejects final/submitted/completed research artifacts that still contain
    raw placeholder tokens.
- `MAP_System/tests/test_validate_research_artifacts.py`
  - Covers a clean temporary Research System template set.
  - Covers a missing required template fragment.
  - Covers a final research summary with unresolved placeholders.
- `MAP_System/scripts/run_tests.sh`
  - Runs the validator and focused test as part of the MAP suite.

## Verification

- `python3 MAP_System/scripts/validate_research_artifacts.py` - PASS.
- `python3 MAP_System/tests/test_validate_research_artifacts.py` - PASS.
- `python3 -m py_compile MAP_System/scripts/validate_research_artifacts.py MAP_System/tests/test_validate_research_artifacts.py` - PASS.

## Notes

This validator is intentionally structural. It does not judge research prose or
source quality itself; it prevents missing templates and malformed final
artifacts from passing silently into project truth.
