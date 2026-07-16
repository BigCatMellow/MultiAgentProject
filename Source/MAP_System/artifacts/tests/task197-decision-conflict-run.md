# TASK-197 Decision Conflict Run

Task: TASK-197
Agent: codex-lab-mozu
Date: 2026-07-15

## Command

```bash
python3 MAP_System/scripts/validate_decisions.py
```

## Result

- Exit code: 0
- Decisions checked: 27
- Hard validation failures: 0
- Report-only conflict notes: 3

## Report-Only Findings

- `SUPERSESSION_ONE_WAY`: `DEC-004` says it is superseded by `DEC-008`, but `DEC-008` does not list `DEC-004` in a reciprocal `Supersedes` field.
- `SUPERSESSION_ONE_WAY`: `DEC-007` says it is superseded by `DEC-008`, but `DEC-008` does not list `DEC-007` in a reciprocal `Supersedes` field.
- `SUPERSESSION_ONE_WAY`: `DEC-012` says it is superseded by `DEC-014`, but `DEC-014` does not list `DEC-012` in a reciprocal `Supersedes` field.

## Triage

These are real metadata cleanup findings, not behavioral decision conflicts. The supersession relationships are already visible in the older decisions' `Status` lines, so no active MAP rule is ambiguous. A later cleanup task can add reciprocal `Supersedes` fields to the replacement decisions if MAP wants the decision log to be mechanically complete.

No same-subject contradiction was reported for the current `shared/decisions.md` pass.

## Focused Verification

```bash
python3 MAP_System/tests/test_decision_conflicts.py
python3 -m py_compile MAP_System/scripts/validate_decisions.py MAP_System/tests/test_decision_conflicts.py
```

Both focused checks passed.
