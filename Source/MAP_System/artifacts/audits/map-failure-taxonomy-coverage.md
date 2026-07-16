# MAP Failure Taxonomy Coverage (TASK-157, Wave 9)

Status: draft-active
Owner: command-center
Built by: TASK-157

## Purpose

This audit maps known MAP validators and tests to multi-agent failure classes,
then identifies missing regression coverage. It is MAST-style in shape:
failure mode first, current detector second, missing test third.

## Coverage Matrix

| Failure class | Example MAP failure | Current coverage | Gap |
|---|---|---|---|
| Task identity collision | two agents create same task ID | `test_map_task_auto_id.py`; SQLite allocator helpers | Add abstract state-machine interleaving test from formal spike. |
| Duplicate active claim | two agents own same task | claims tests; `agent_loop.py` lease helpers; task mirror validator | Add race fixture with two simultaneous claim attempts against same DB. |
| Output path collision | active tasks share non-shared output path | `validate_task_graph.py`; `test_validate_task_graph_shared_outputs.py` | Add decomposer fixture that emits colliding paths before task creation. |
| Dependency cycle | task graph cannot progress | `validate_task_graph.py` cycle detection | Add edge-metadata cycle fixtures when dependency DAG metadata lands. |
| Unknown dependency | task waits on absent ID | `validate_task_graph.py` unknown dependency check | Add decomposer unresolved-dependency regression test. |
| Event schema drift | malformed/legacy event fields | `validate_events.py`; `test_validate_events.py` | Add protocol-output malformed event fixture from TASK-152. |
| SQLite/file mirror drift | exported task JSON disagrees with DB | `validate_task_mirrors.py`; `test_validate_task_mirrors.py`; `test_exporter_invariants.py` | Add interrupted-export chaos fixture. |
| Review/self-review breach | task author reviews own work | `validate_review.py`; `test_no_self_review.py` | Add review assignment pre-dispatch checker test. |
| Approval gate bypass | task release without required review/gate | `test_release_gate.py`; `test_review_gate.py`; `multigate_regression_test.py` | Add runner route test for policy-check `require_approval`. |
| Agent liveness stall | claimed task silently stops | `limit_watcher.py`; `test_limit_watcher.py`; `reconcile_agents.py` | Add reaper/dead-letter chaos fixture once queue exists. |
| Retry storm | failing handler loops too fast | `agent_loop.py` retry cooldown; `agent-loop-retry-cooldown-test.md` | Add executable test asserting cooldown suppresses immediate reclaim. |
| Local helper misuse | helper/local lane gets final authority | TASK-153 specs; TASK-156 test plan | Implement capability whitelist tests. |
| Destructive action before approval | hard-to-reverse command assigned as ordinary work | policy docs only | Implement pre-dispatch destructive-action gate tests. |
| Secret or external-service leak | secret written to durable file or uploaded | security prose; no specific validator | Add secret-pattern scanner for durable MAP files and connector upload review checklist. |
| Context compression drift | stale summary overrides durable truth | startup/handoff rules; no direct validator | Add handoff/context packet validator for required task/status/event references. |
| Committed poisoned state | bad state reaches canonical store | validators catch some classes; self-repair records | Add rollback/reconcile probe from TASK-155 chaos plan. |
| Operator bottleneck | gated requests accumulate or stall work | hcom discipline; runner gates | Add metrics/report for pending requests, gate age, and unattended-safe work. |
| Multi-project bleed | global MAP state overwrites project-local state | `docs/project-map.md`; project-local task graphs | Add multi-project fixture with reusable MAP plus Pathwell-local MAP. |
| CommandCenterUI bypass | UI writes state without CLI checks | TASK-150 UI spec; no enforcement test | Add backend contract tests before UI intervention controls become write-capable. |

## Existing Strong Areas

Strongest current coverage:

- task graph structure;
- task mirror/export consistency;
- event schema warnings/errors;
- review/no-self-review record shape;
- release gate behavior;
- risk, research, repair, and shared-state document validators.

These are useful because they are executable and run against real repository
state, not only simulation assumptions.

## Missing Regression Tests

Highest-value missing tests:

1. `test_policy_checker_capability_whitelist.py` for TASK-156 allow,
   require-approval, and reject outcomes.
2. `test_agent_loop_dead_letter_resume.py` for killed handler and replay
   behavior from TASK-155.
3. `test_export_interruption_reconcile.py` for stale mirror recovery.
4. `test_decomposer_dependency_edges.py` for unresolved dependency, cycle, and
   artifact-edge validation.
5. `test_context_summary_drift.py` for compressed handoff missing blocker or
   stale task state.
6. `test_multi_project_isolation.py` for root MAP vs. Pathwell-local MAP
   state separation.
7. `test_command_center_ui_backend_policy.py` before write-capable UI controls.

## Coverage Judgment

MAP has good structural validators for the current file/SQLite task system.
The weakest areas remain the same ones named by the 6.13 gap register:
semantic validator quality, decomposer correctness, committed-state recovery,
human/operator load, multi-project isolation, and trust-boundary enforcement.

The next implementation wave should prioritize tests that run against real MAP
fixtures, not more simulation-only harnesses.
