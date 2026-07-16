# Review Record: TASK-116

## Header

```text
task_id:      TASK-116
reviewer:     codex-lab-lema
review_date:  2026-07-03
task_owner:   codex-lab-dino
```

Reviewer != owner. Independence check passes.

## Verdict

```text
CHANGES_REQUESTED
```

## Acceptance Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `graph/runner.py` treats `RELEASED` dependencies as satisfied consistently with `validate_task_graph.py` terminal status semantics | FAIL | The implementation also treats `RETIRED` as dependency-satisfying. TASK-100 explicitly established that `RETIRED` is terminal for validation/stall cleanup but must not satisfy dependency expectations of completed output. |
| 2 | Runner task-classification tests cover READY tasks whose dependencies are `RELEASED` | PASS | `test_released_dependency_satisfies_ready_task` covers `RELEASED`. |
| 3 | Focused runner classification test, `validate_task_graph.py`, `validate_repair_artifacts.py`, and full `run_tests.sh` pass | PARTIAL | Focused runner classification and repair validator pass under the project venv, but the focused test suite lacks a regression proving a `RETIRED` dependency remains unsatisfied. |

## Files Reviewed

- `MAP_System/graph/runner.py`
- `MAP_System/tests/test_runner_task_classification.py`
- `MAP_System/repairs/REPAIR-0001-runner-released-dependency-drift.md`
- `MAP_System/artifacts/tests/task-116-runner-released-dependencies.md`
- `MAP_System/scripts/validate_task_graph.py`
- `MAP_System/artifacts/reviews/task100-review-lema.md`
- `MAP_System/artifacts/releases/task-100-release-checklist.md`

## Findings

| Severity | File | Finding | Required Action |
|---|---|---|---|
| REQUIRED | `MAP_System/graph/runner.py` | `DEPENDENCY_SATISFIED_STATUSES` includes `RETIRED`, making retired duplicate/cancelled tasks satisfy downstream dependencies. This directly conflicts with TASK-100's policy that `RETIRED` is terminal-by-decision but never dependency-satisfying. | Remove `RETIRED` from the runner dependency-satisfied set. Keep `RELEASED` as dependency-satisfying. |
| REQUIRED | `MAP_System/tests/test_runner_task_classification.py` | The regression suite covers `RELEASED` dependencies but does not protect the existing TASK-100 `RETIRED` dependency behavior. | Add a test proving a READY task depending on a `RETIRED` task is not routed to `ready_tasks` and remains blocked/waiting on dependency. |
| REQUIRED | `MAP_System/repairs/REPAIR-0001-runner-released-dependency-drift.md` | The repair record states the fix made `RETIRED` dependency-satisfying, which is the invalid part of the implementation. | Update the repair record to say `RELEASED` was added while `RETIRED` remains non-dependency-satisfying per TASK-100. |

## Forbidden Changes Check

- Do not change `validate_task_graph.py`'s TASK-100 terminal/stall semantics.
- Do not make `RETIRED` dependency-satisfying.
- Do not weaken the existing `BLOCKED` task regression.

## Verification

```bash
MAP_System/.venv/bin/python MAP_System/tests/test_runner_task_classification.py
MAP_System/.venv/bin/python -c "from MAP_System.graph.runner import evaluate_tasks; state={'tasks':[{'task_id':'TASK-A','status':'RETIRED','dependencies':[],'task_type':'maintenance','role':'state_steward','title':'retired duplicate','description':'','acceptance_criteria':[]},{'task_id':'TASK-B','status':'READY','dependencies':['TASK-A'],'task_type':'implementation','role':'implementer','title':'dependent','description':'','acceptance_criteria':[]}], 'agents':{}}; r=evaluate_tasks(state); print({'done_task_ids': r['done_task_ids'], 'ready_tasks': r['ready_tasks'], 'blocked_tasks': r['blocked_tasks']})"
python3 MAP_System/scripts/validate_repair_artifacts.py
```

Results:

```text
focused runner classification tests: PASS
RETIRED dependency check: {'done_task_ids': ['TASK-A'], 'ready_tasks': ['TASK-B'], 'blocked_tasks': []}
repair validator: PASS
```

The RETIRED dependency check is the failing behavior: `TASK-B` should not be
ready when its only dependency is a retired duplicate/cancelled card.

## Notes

The core idea of TASK-116 is correct: `RELEASED` tasks should satisfy
dependencies. The required fix is narrow: add `RELEASED` without broadening
dependency satisfaction to `RETIRED`.
