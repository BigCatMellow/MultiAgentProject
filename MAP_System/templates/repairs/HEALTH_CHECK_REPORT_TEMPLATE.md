# Health Check Report

Health ID: HEALTH-0001
Run by: <agent-name>
Date: <YYYY-MM-DD>
Status: CLEAN / FINDINGS_FILED

Read-only snapshot. Do not apply fixes while producing this report — file
Repair Records separately for anything found.

## Checks run

| Check | Command | Result | Notes |
|---|---|---|---|
| Shared-state metadata | `scripts/validate_shared_state.py` | PASS/FAIL | |
| Decision log | `scripts/validate_decisions.py` | PASS/FAIL | |
| Task graph | `scripts/validate_task_graph.py` | PASS/FAIL | |
| Event log shape | `scripts/validate_events.py` | PASS/FAIL | |
| Agent status reconciliation | `scripts/reconcile_agents.py` | PASS/FAIL | |
| Emergence stale report | `scripts/map_emergence.py stale` | PASS/FAIL | |
| Task-flow metrics | `scripts/map_metrics.py` | PASS/FAIL | |
| Local assistant health | `scripts/local_assistant_health.py` | PASS/FAIL | |
| Exporter/mirror invariants | `tests/test_exporter_invariants.py` | PASS/FAIL | |

## Findings requiring a Repair Record

<List anything that was not a clean PASS above, with severity classification
per MAP_System/SELF_REPAIR_SYSTEM.md. Link the Repair Record once filed.>

-

## Overall assessment

<One or two sentences: is MAP internally consistent right now? Anything
command-center should know about immediately (STRUCTURAL findings)?>

## Notes

-
