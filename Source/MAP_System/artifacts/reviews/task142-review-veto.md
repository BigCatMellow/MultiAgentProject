# Review: TASK-142 Broadcast Coordinator + Research Decision + Event Warning Baseline

task_id: TASK-142
task_owner: claude-lab-magi
reviewer: codex-lab-veto
date: 2026-07-04

## Verdict

CHANGES_REQUESTED

Two REQUIRED findings block approval. The broadcast-coordinator convention and
event-warning baseline mechanism look directionally correct, but the Research
decision is not yet valid durable state and one touched file is missing from
the task's declared output paths.

## Acceptance Criteria Check

| # | Result | Evidence |
|---|---|---|
| 1 | PASS | `MAP_System/AGENTS.md` adds "Broadcast Coordinator Convention"; `MAP_System/notes/helper-agent-guide.md` points core-agent broadcast ownership there instead of mixing it with helper routing. |
| 2 | FAIL | DEC-027 exists in `MAP_System/shared/decisions.md`, but `validate_decisions.py` fails because the entry is missing `Applies-To`. |
| 3 | PASS | `validate_events.py` loads `MAP_System/events/warning_baseline.json`, splits legacy vs new warnings, supports `--fail-on-new`, and `scripts/run_tests.sh` runs that mode. |

## Files Reviewed

- `MAP_System/AGENTS.md`
- `MAP_System/notes/helper-agent-guide.md`
- `MAP_System/shared/decisions.md`
- `MAP_System/RESEARCH_SYSTEM.md`
- `MAP_System/artifacts/research/README.md`
- `MAP_System/events/warning_baseline.json`
- `MAP_System/scripts/validate_events.py`
- `MAP_System/tests/test_validate_events.py`
- `MAP_System/scripts/run_tests.sh`
- `MAP_System/tasks/TASK-142.json`

## Forbidden Changes Check

- PASS: no self-review; reviewer `codex-lab-veto` is not owner `claude-lab-magi`.
- FAIL: `MAP_System/shared/decisions.md` was substantively edited for DEC-027 but is not in `TASK-142` output paths.
- PASS: no hidden helper, destructive action, external-service use, or broad Git operation is part of the reviewed change.

## Findings

### REQUIRED: Register `MAP_System/shared/decisions.md` in TASK-142 output paths

`TASK-142` acceptance criterion #2 is satisfied through a new DEC-027 entry in
`MAP_System/shared/decisions.md`, but `TASK-142.json` does not list that file in
`output_paths`.

Impact: reviewers and release checks cannot rely on the task's declared scope;
this repeats the output-path drift class TASK-140/TASK-141 were trying to
remove.

Required fix: use the sanctioned task tooling to add
`MAP_System/shared/decisions.md` to `TASK-142` output paths, then export/validate
the mirrors.

### REQUIRED: Add the missing `Applies-To` field to DEC-027

`python3 MAP_System/scripts/validate_decisions.py` fails:

```text
FAIL DEC-027: Research System Stays Specification-Only Until A Real Research Question Exists: MISSING_FIELD: applies_to
```

Impact: the Research decision is not valid durable decision state yet.

Required fix: add an `Applies-To:` line to DEC-027 and rerun
`validate_decisions.py`.

## Verification

Commands run:

```text
python3 MAP_System/scripts/validate_events.py --json
python3 MAP_System/scripts/validate_events.py --fail-on-new
python3 MAP_System/scripts/validate_shared_state.py --shared-dir MAP_System/shared
python3 MAP_System/scripts/validate_task_mirrors.py
python3 MAP_System/scripts/validate_decisions.py
```

Results:

- `validate_events.py --fail-on-new`: pass, 33 legacy warnings, 0 new warnings.
- `validate_shared_state.py`: pass, 19 files checked.
- `validate_task_mirrors.py`: pass.
- `validate_decisions.py`: fail on DEC-027 missing `Applies-To`.
