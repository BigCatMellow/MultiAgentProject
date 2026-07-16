# Repair Record

Repair ID: REPAIR-0001
Related task: <TASK_ID or NONE>
Found by: <agent-name>
Date: <YYYY-MM-DD>
Severity: COSMETIC / DRIFT / BLOCKING / STRUCTURAL
Status: APPLIED / PROPOSED / APPROVED / REJECTED

## What was found

<Concrete description: which file/state disagreed with which other
file/state, or what check failed.>

## Surfaced by

<Which validator, script, or manual observation found this:
e.g. `scripts/validate_task_graph.py`, review finding, session resume.>

## Severity rationale

<Why this severity, per MAP_System/SELF_REPAIR_SYSTEM.md's table. State
blast radius and reversibility.>

## Proposed or applied fix

<What was changed, or what is proposed if this requires approval first.>

## Authority check

- [ ] DRIFT or mechanical BLOCKING — core agent applied directly
- [ ] Judgment-requiring BLOCKING — proposed via hcom before applying
- [ ] STRUCTURAL — proposed to command-center, not yet applied without approval

## Verification

<Which validators/tests were re-run after the fix, and their result. Minimum:
the validator that surfaced the issue, plus validate_task_graph.py and
test_exporter_invariants.py if task/mirror state was touched.>

## Recurrence check

- [ ] First occurrence of this drift class
- [ ] Repeat — logged in `shared/improvement-backlog.md`: <link or NONE yet>
- [ ] Repeat — permanent fix proposed (validator/template/decision): <link or PENDING>

## Notes

-
