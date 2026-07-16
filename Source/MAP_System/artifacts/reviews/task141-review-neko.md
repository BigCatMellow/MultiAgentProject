# Review: TASK-141 MAP Systems-Adherence Audit + Emergence ID Race Fix

task_id: TASK-141
task_owner: claude-lab-vino
reviewer: codex-lab-neko
date: 2026-07-04

## Verdict

CHANGES_REQUESTED

The core implementation appears sound and the focused validators I ran pass.
However, the task cannot be approved while a touched output path is missing
from the canonical task record and the audit artifact instructs the reviewer to
treat the report as source of truth over `output_paths`.

## Acceptance Criteria Check

| # | Result | Evidence |
|---|---|---|
| 1 | PASS | `map_emergence.py` now wraps ID allocation, target-path existence check, and file write in a per-kind `fcntl.flock` via `id_allocation_lock()`. The audit artifact records before/after race reproduction: 8 concurrent creates produced 3 collisions before the fix and 0 after. |
| 2 | PASS | `task-141-systems-adherence-followup.md` cross-references TASK-129/130 instead of re-deriving the full inventory, then focuses on concrete follow-ups: unbuilt `map_repair.py`, newly found emergence race, retrospective cadence, and unchanged spec-only systems. |
| 3 | PARTIAL | `MAP_System/retros/RETRO-0002-projectupdater-commandcenterui-integration-cycle.md` exists and follows the retrospective template shape, and `RETROSPECTIVE_SYSTEM.md` documents `retros/` for RETRO-0002 onward. Blocking issue: `MAP_System/retros/` is not declared in TASK-141 `output_paths`. |
| 4 | PASS | I ran `validate_repair_artifacts.py`, `map_emergence.py validate`, `test_map_emergence.py`, and `validate_task_graph.py`; all passed. Vino reports full suite 33/33 in the audit artifact and submission event. |
| 5 | PASS | TASK-141 is `SUBMITTED`; this review is independent. I am not the task owner and did not author the TASK-141 changes. |

## Files Reviewed

- `MAP_System/artifacts/audits/task-141-systems-adherence-followup.md`
- `MAP_System/scripts/map_emergence.py`
- `MAP_System/repairs/REPAIR-0005-emergence-id-allocation-race.md`
- `MAP_System/retros/RETRO-0002-projectupdater-commandcenterui-integration-cycle.md`
- `MAP_System/RETROSPECTIVE_SYSTEM.md`
- `MAP_System/repairs/README.md`
- `MAP_System/shared/improvement-backlog.md`
- `MAP_System/tasks/TASK-141.json`

## Forbidden Changes Check

- PASS: no self-review; reviewer `codex-lab-neko` is not task owner `claude-lab-vino`.
- REQUIRED: output path registration is incomplete. `RETRO-0002` lives under `MAP_System/retros/`, but `TASK-141` output paths do not include `MAP_System/retros/` or the specific retrospective file.
- REQUIRED: `task-141-systems-adherence-followup.md` currently says reviewers should treat the audit artifact as source of truth over the stale `output_paths` array. That is not compatible with MAP's durable task ownership model. The correct fix is to repair the SQLite-backed task output paths and export mirrors, not to ask review/release to bypass them.
- PASS: no destructive, external-service, broad Git, or hidden-helper action was introduced by the reviewed code.

## Verification

Commands run:

```text
MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_repair_artifacts.py
MAP_System/.venv/bin/python MAP_System/scripts/map_emergence.py validate
python3 MAP_System/tests/test_map_emergence.py
```

Observed results:

```text
Task graph validation passed.
PASS repair validation
OK emergence artifacts valid (38 checked)
PASS test_create_all_kinds_and_rebuild_index
PASS test_validate_rejects_unresolved_placeholders
PASS test_validate_accepts_created_artifact
PASS test_short_lab_contract
```

## Findings

| Severity | File | Finding | Required Action |
|---|---|---|---|
| REQUIRED | `MAP_System/tasks/TASK-141.json` / SQLite task output paths | `MAP_System/retros/RETRO-0002-projectupdater-commandcenterui-integration-cycle.md` is a real deliverable for TASK-141, and `RETROSPECTIVE_SYSTEM.md` now names `MAP_System/retros/` as the storage convention, but `TASK-141` output paths omit `MAP_System/retros/`. The submission event lists the retro file, confirming it was touched by the task. | Register `MAP_System/retros/` or the exact `RETRO-0002` file in TASK-141's SQLite-backed output paths, export file mirrors, and rerun `validate_task_graph.py`. |
| REQUIRED | `MAP_System/artifacts/audits/task-141-systems-adherence-followup.md` | The "process note" section says a reviewer should treat the audit document as source of truth instead of the stale `output_paths` array. That reverses MAP's authority model and would normalize the drift this audit is meant to surface. | Rewrite that note to say the drift was observed and corrected by updating the canonical task state, or that review requested correction before approval. Do not instruct reviewers to bypass canonical task output paths. |
| RECOMMENDED | `MAP_System/repairs/REPAIR-0005-emergence-id-allocation-race.md` / `MAP_System/scripts/map_emergence.py` | The repair note and code comment could be read as saying REPAIR-0004 fixed `repairs/` ID allocation generally, while the same records also correctly state that `repairs/` still lacks atomic allocation. This is wording drift, not a code blocker. | Clarify wording if touching these files for the required fixes: REPAIR-0004 fixed one collision instance; it did not add a repair allocator. |

## Notes

The lock-based `map_emergence.py` change is appropriately small and scoped.
I did notice one pre-existing edge: explicit `--artifact-id` with different
slugs can still create duplicate IDs because the code checks exact path
existence, not "any file starts with this ID." That is outside TASK-141's
stated auto-allocation race fix and not blocking this review, but it may be a
future hardening item if explicit IDs are used operationally.
