# Review: TASK-176 Prune Stale RnS Incidents For Absent Sessions

```
task_id:      TASK-176
reviewer:     claude-lab-zera
review_date:  2026-07-14
task_owner:   codex-lab-mozu
```

Reviewer (claude-lab-zera) != task owner (codex-lab-mozu). Independence
check passes.

## Verdict

```
APPROVED
```

## Acceptance Criteria Check

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | limit_watcher prunes open incidents for agents absent from both durable status.json and current hcom snapshot before probe actions are computed | PASS | `prune_absent_session_tracking()` computes `known_agents = status_data.agents ∪ snapshot` and drops any `incidents` entry not in that set; wired into `main()`'s loop before `live_now`/incident-detection logic runs (correct ordering — prune first, then decide). |
| 2 | limit_watcher filters last_live to durable-or-current hcom agents so stale helper names do not create new presumed-down incidents | PASS | Same function also filters `state["last_live"]` to `known_agents`, returning both `pruned_incidents` and `pruned_last_live` for logging. |
| 3 | Focused tests cover pruning without suppressing durable registered agents, and dry-run no longer probes TASK-175's stale historical names | PASS | `test_prune_absent_session_tracking_removes_historical_helpers` (removes truly-stale names) and `test_prune_preserves_registered_agent_for_presumed_down_detection` (a durable-registered-but-hcom-absent agent is correctly NOT pruned, and still detected as presumed-down) — these are the two cases that actually matter, both covered. |
| 4 | Task uses only MAP_System files and does not edit external CommandCenterUI | PASS | Both declared output paths are `MAP_System/scripts/limit_watcher.py` and `MAP_System/tests/test_limit_watcher.py`; no external paths touched. |

## Files Reviewed

- `MAP_System/scripts/limit_watcher.py`
- `MAP_System/tests/test_limit_watcher.py`
- `MAP_System/tasks/TASK-176.json`

## Forbidden Changes Check

- PASS: no self-review; reviewer `claude-lab-zera` is not owner `codex-lab-mozu`.
- PASS: changed files match declared output paths.
- PASS: pruning only runs when `snapshot is not None` (hcom actually
  reachable) — avoids pruning off incomplete data if hcom itself is down,
  a sensible safety guard I confirmed by reading the call site.

## Verification

Commands run:

```bash
python3 MAP_System/tests/test_limit_watcher.py
bash MAP_System/scripts/run_tests.sh
python3 MAP_System/scripts/validate_task_mirrors.py
```

Results: `test_limit_watcher.py` 18/18 (including both new prune tests).
Full suite pass=54 fail=0 total=54. Task mirrors pass.

## Findings

No BLOCKER or REQUIRED findings.

## Notes

Correctly scoped and directly answers TASK-175's own finding #3. The two
new tests are the right two: one proves stale noise actually gets removed,
the other proves the fix doesn't overcorrect into hiding a real
presumed-down incident. Good discipline keeping this narrowly focused on
the RnS gap rather than expanding into the mission-control liveness or
CommandCenterUI gaps TASK-175 also found — those are correctly separate
follow-on tasks (TASK-177/178, etc.).
