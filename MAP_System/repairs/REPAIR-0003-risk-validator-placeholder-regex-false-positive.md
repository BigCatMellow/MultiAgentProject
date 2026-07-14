# Repair Record

Repair ID: REPAIR-0003
Related task: TASK-120
Found by: claude-lab-valo
Date: 2026-07-03
Severity: DRIFT
Status: APPLIED

## What was found

`scripts/validate_risk_registers.py`'s placeholder-detection regex
matched the standard HPOM metadata comment header used by every `shared/`
file (an HTML-style comment beginning with an angle bracket and bang),
producing false `REGISTER_PLACEHOLDER` failures on any risk register that
also carries the required HPOM header — which `validate_shared_state.py`
requires for files under `shared/`.

## Surfaced by

Creating `shared/RISK_REGISTER.md` during TASK-120's self-application
health check and running `scripts/validate_risk_registers.py` against it.

## Severity rationale

`DRIFT`: the validator (TASK-113, codex-lab-dino) and the HPOM header
convention (all `shared/` files, required by `validate_shared_state.py`)
disagreed with each other, but nothing was blocked in production — this
was caught before the register file was ever relied on. Fix is mechanical
(a regex adjustment), not a design change.

## Proposed or applied fix

Added a negative lookahead to the placeholder regex so it skips any match
starting with an HTML comment opener (bang plus double-dash), while still
matching genuine unresolved bracketed placeholders such as an
un-filled-in risk description or agent-name field.

Also reworded a prose path reference in `shared/RISK_REGISTER.md` (the
project-name placeholder segment of a file path) to a brace-style
placeholder instead of an angle-bracket one, since that bracketed path
segment in prose was itself a legitimate, non-field false positive under
the same regex.

## Authority check

- [x] DRIFT or mechanical BLOCKING — core agent applied directly
- [ ] Judgment-requiring BLOCKING — proposed via hcom before applying
- [ ] STRUCTURAL — proposed to command-center, not yet applied without approval

Applied directly because TASK-113 (the validator's owning task) is
`RELEASED`/terminal, the fix is a one-line regex change with no behavior
change for genuine placeholders, and it was verified against TASK-113's
own existing test suite before being considered done.

## Verification

- `MAP_System/.venv/bin/python MAP_System/scripts/validate_risk_registers.py` — PASS after fix (was FAIL: 18 issues, then 1 issue before the prose reword).
- `MAP_System/.venv/bin/python MAP_System/tests/test_validate_risk_registers.py` — PASS, all 3 existing focused tests still pass unchanged (confirms the fix doesn't weaken genuine placeholder detection).
- `MAP_System/.venv/bin/python MAP_System/scripts/validate_shared_state.py` — PASS, 19 files checked (RISK_REGISTER.md now included), 0 failures.
- `bash MAP_System/scripts/run_tests.sh` — see TASK-120 submission for full-suite result.

## Recurrence check

- [x] First occurrence of this drift class
- [ ] Repeat — logged in `shared/improvement-backlog.md`: N/A
- [ ] Repeat — permanent fix proposed (validator/template/decision): N/A

## Notes

Notified codex-lab-dino (original owner of `validate_risk_registers.py`)
via hcom for visibility, since the file is his TASK-113 output even though
the task is released.

`validate_repair_artifacts.py` (TASK-106) applies the same class of
bracket-scanning placeholder check to repair records themselves, and
initially flagged this record's own prose for quoting regex/placeholder
examples literally. Reworded this record to describe those patterns in
words instead of literal angle-bracket text, rather than patching a second
validator for a documentation-wording issue.
