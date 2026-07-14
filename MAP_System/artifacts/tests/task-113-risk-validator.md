# TASK-113 Risk Register Validator

task_id: TASK-113
owner: codex-lab-dino
date: 2026-07-03

## Scope

Added focused validation tooling for the Risk System register structure created
by TASK-111. The validator checks the template and risk register artifact shape
without owning or rewriting `MAP_System/RISK_SYSTEM.md` prose.

## Files

- `MAP_System/scripts/validate_risk_registers.py`
- `MAP_System/tests/test_validate_risk_registers.py`
- `MAP_System/scripts/run_tests.sh`

## Validation coverage

- Required `templates/RISK_REGISTER_TEMPLATE.md` fragments are present.
- MAP-system and project-level risk register artifacts are named
  `RISK_REGISTER.md`, are non-empty, and contain required register fields and
  sections.
- Register `Class`, `Severity`, and `Status` fields use the enum values defined
  by TASK-111.
- Register artifacts fail if unresolved `<placeholder>` text remains.
- Focused tests cover a passing template-only case, a missing template
  fragment, and a register with placeholders.

## Commands

- `MAP_System/.venv/bin/python MAP_System/scripts/validate_risk_registers.py`
  - PASS: risk register validation
- `MAP_System/.venv/bin/python MAP_System/tests/test_validate_risk_registers.py`
  - PASS: focused risk register validator tests
- `MAP_System/.venv/bin/python -m py_compile MAP_System/scripts/validate_risk_registers.py MAP_System/tests/test_validate_risk_registers.py`
  - PASS
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_repair_artifacts.py`
  - PASS: REPAIR-0001 remains valid
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py`
  - PASS
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py`
  - PASS: 0 errors, 33 known legacy warnings
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_shared_state.py --shared-dir MAP_System/shared`
  - PASS: 18 files checked, 0 failures, 0 warnings
- `MAP_System/scripts/run_tests.sh`
  - PASS: 33 passed, 0 failed
