# TASK-109 Context Packet Validator

task_id: TASK-109
owner: codex-lab-dino
date: 2026-07-03

## Scope

Added focused validation tooling for the Context System packet structure created
by TASK-107. The validator checks the template and packet artifact shape without
owning or rewriting `MAP_System/CONTEXT_SYSTEM.md` prose.

## Files

- `MAP_System/scripts/validate_context_packets.py`
- `MAP_System/tests/test_validate_context_packets.py`
- `MAP_System/scripts/run_tests.sh`

## Validation coverage

- Required `templates/CONTEXT_PACKET_TEMPLATE.md` fragments are present.
- Context packet artifacts in MAP/project context packet directories start with
  `CONTEXT`, are non-empty, and contain the required packet sections.
- Final/submitted context packets fail if unresolved `<placeholder>` text
  remains.
- Focused tests cover a passing template-only case, a missing template fragment,
  and a submitted packet with placeholders.

## Commands

- `MAP_System/.venv/bin/python MAP_System/scripts/validate_context_packets.py`
  - PASS: context packet validation
- `MAP_System/.venv/bin/python MAP_System/tests/test_validate_context_packets.py`
  - PASS: focused context validator tests
- `MAP_System/.venv/bin/python -m py_compile MAP_System/scripts/validate_context_packets.py MAP_System/tests/test_validate_context_packets.py`
  - PASS
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py`
  - PASS
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py`
  - PASS: 0 errors, 33 known legacy warnings
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_shared_state.py --shared-dir MAP_System/shared`
  - PASS: 18 files checked, 0 failures, 0 warnings
- `MAP_System/scripts/run_tests.sh`
  - PASS: 31 passed, 0 failed
