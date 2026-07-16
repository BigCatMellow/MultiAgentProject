# Review: TASK-178 Refresh Mission-Control Roster From Live hcom

```
task_id:      TASK-178
reviewer:     claude-lab-zera
review_date:  2026-07-14
task_owner:   codex-lab-mozu
```

Reviewer (claude-lab-zera) != task owner (codex-lab-mozu). Independence
check passes. (This touches `mission_control_tui.py`/`test_mission_control_tui.py`,
which I also own from TASK-160/164/174 — reviewing someone else's edit to
my own file is fine; self-review only means I can't review my own PR.)

## Verdict

```
APPROVED
```

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Mission-control roster can be built from raw live hcom list JSON without writing canonical MAP state | PASS | `get_live_liveness_snapshot()` calls `get_hcom_list_json()` (subprocess `hcom list --json`, read-only) then composes `normalize_hcom_status()` + `build_snapshot` (aliased `build_liveness_records`). Structural no-write test (`test_module_never_writes_to_map_state`) still passes unchanged. |
| 2 | Dashboard snapshot prefers live hcom-derived liveness when available and falls back to shared/liveness-state.md when unavailable | PASS | `get_roster()`'s logic: try live first, fall back to markdown if empty/unavailable. `test_get_roster_prefers_live_and_falls_back_to_markdown` proves both branches via monkeypatching. `get_hcom_list_json()` fails soft to `None` on `OSError`/timeout/non-zero exit/bad JSON — real defensive read, not a happy-path-only assumption. |
| 3 | Tests prove the implementation composes liveness_reaper helpers rather than duplicating liveness classification logic | PASS | `test_live_liveness_snapshot_composes_reaper_helpers` monkeypatches `normalize_hcom_status`/`build_liveness_records` and asserts they're actually called — proves composition, not just correct output that could coincidentally match a reimplementation. |
| 4 | Read-only structural guards still pass; no external CommandCenterUI edits | PASS | Both structural no-write tests (data layer + rendering layer) still pass. No CommandCenterUI paths in output_paths or touched files. |

## Independent Verification

Ran the live roster against the real repo (not just fixtures):

```bash
python3 MAP_System/scripts/mission_control_tui.py --json
```

Confirmed `claude-lab-zera` and `codex-lab-mozu` both show
`state: alive, evidence: hcom:active` — correctly reflecting real, live hcom
state instead of the stale `shared/liveness-state.md` markdown snapshot
TASK-175 flagged as the gap.

## Files Reviewed

- `MAP_System/scripts/mission_control_tui.py`
- `MAP_System/tests/test_mission_control_tui.py`
- `MAP_System/tasks/TASK-178.json`

## Forbidden Changes Check

- PASS: no self-review; reviewer `claude-lab-zera` is not owner `codex-lab-mozu`.
- PASS: changed files match declared output paths.
- PASS: no external CommandCenterUI edits.
- PASS: does not touch or conflict with TASK-179's concurrent edits to
  `librarian.py`/wikilink docs (different files entirely).

## Verification

Commands run:

```bash
python3 MAP_System/scripts/mission_control_tui.py --json
python3 MAP_System/tests/test_mission_control_tui.py
bash MAP_System/scripts/run_tests.sh
```

Results: live roster correctly shows real hcom-derived states for known
active agents. Focused tests all pass (including 3 new ones covering the
live path, fallback, and composition). Full suite pass=54 fail=0 total=54.

## Findings

No BLOCKER or REQUIRED findings.

## Notes

This directly closes TASK-175's finding #1 (mission-control liveness using
stale markdown by default) using TASK-177's fix as the building block,
exactly the sequencing the runtime-exercise report recommended. Good
defensive coding on `get_hcom_list_json()` — every real failure mode
(hcom not installed, timeout, non-zero exit, malformed JSON) fails soft to
the markdown fallback rather than crashing the dashboard.
