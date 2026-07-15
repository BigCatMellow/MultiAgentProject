#!/bin/sh
set -u

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$ROOT/.."

PASS=0
FAIL=0

run_check() {
  name="$1"
  shift
  printf 'RUN %s\n' "$name"
  if "$@"; then
    PASS=$((PASS + 1))
    printf 'PASS %s\n\n' "$name"
  else
    FAIL=$((FAIL + 1))
    printf 'FAIL %s\n\n' "$name"
  fi
}

py_compile_all() {
  find MAP_System -path MAP_System/.venv -prune -o -type f -name '*.py' -print0 \
    | xargs -0 -r python3 -m py_compile
}

run_check py_compile py_compile_all
run_check validate_task_mirrors python3 MAP_System/scripts/validate_task_mirrors.py
run_check validate_task_graph python3 MAP_System/scripts/validate_task_graph.py
run_check validate_canonical_repo_paths python3 MAP_System/scripts/validate_canonical_repo_paths.py
run_check validate_research_artifacts python3 MAP_System/scripts/validate_research_artifacts.py
run_check validate_repair_artifacts python3 MAP_System/scripts/validate_repair_artifacts.py
run_check validate_context_packets python3 MAP_System/scripts/validate_context_packets.py
run_check validate_risk_registers python3 MAP_System/scripts/validate_risk_registers.py
run_check promote_task_test python3 MAP_System/tests/test_promote_task.py
run_check no_self_review_test python3 MAP_System/tests/test_no_self_review.py
run_check exporter_hpom_fields_test python3 MAP_System/tests/test_exporter_hpom_fields.py
run_check exporter_invariants_test python3 MAP_System/tests/test_exporter_invariants.py
run_check review_gate_test python3 MAP_System/tests/test_review_gate.py
run_check release_gate_test python3 MAP_System/tests/test_release_gate.py
run_check map_metrics_test python3 MAP_System/tests/test_map_metrics.py
run_check map_metrics_aliases_test python3 MAP_System/tests/test_map_metrics_aliases.py
run_check outcome_feedback_test python3 MAP_System/tests/test_outcome_feedback.py
run_check map_emergence_test python3 MAP_System/tests/test_map_emergence.py
run_check intake_request_test python3 MAP_System/tests/test_intake_request.py
run_check map_task_auto_id_test python3 MAP_System/tests/test_map_task_auto_id.py
run_check map_task_rework_test python3 MAP_System/tests/test_map_task_rework.py
run_check map_task_add_output_path_test python3 MAP_System/tests/test_map_task_add_output_path.py
run_check map_emergence_stale_test python3 MAP_System/tests/test_map_emergence_stale.py
run_check validate_task_graph_shared_outputs_test python3 MAP_System/tests/test_validate_task_graph_shared_outputs.py
run_check validate_task_mirrors_test python3 MAP_System/tests/test_validate_task_mirrors.py
run_check validate_research_artifacts_test python3 MAP_System/tests/test_validate_research_artifacts.py
run_check validate_repair_artifacts_test python3 MAP_System/tests/test_validate_repair_artifacts.py
run_check map_repair_test python3 MAP_System/tests/test_map_repair.py
run_check validate_context_packets_test python3 MAP_System/tests/test_validate_context_packets.py
run_check validate_risk_registers_test python3 MAP_System/tests/test_validate_risk_registers.py
run_check validate_events_test python3 MAP_System/tests/test_validate_events.py
run_check event_trace_test python3 MAP_System/tests/test_event_trace.py
run_check session_replay_test python3 MAP_System/tests/test_session_replay.py
run_check validate_events_no_new_warnings python3 MAP_System/scripts/validate_events.py --fail-on-new
run_check git_operation_lock_test python3 MAP_System/tests/test_git_operation_lock.py
run_check reconcile_agents_test python3 MAP_System/tests/test_reconcile_agents.py
run_check halt_state_test MAP_System/.venv/bin/python MAP_System/tests/test_halt_state.py
run_check cost_governance_test MAP_System/.venv/bin/python MAP_System/tests/test_cost_governance.py
run_check cost_yield_test python3 MAP_System/tests/test_cost_yield.py
run_check redaction_test python3 MAP_System/tests/test_redaction.py
run_check runner_task_classification_test MAP_System/.venv/bin/python MAP_System/tests/test_runner_task_classification.py
run_check limit_watcher_test python3 MAP_System/tests/test_limit_watcher.py
run_check liveness_reaper_test python3 MAP_System/tests/test_liveness_reaper.py
run_check validate_layer1_test python3 MAP_System/tests/test_validate_layer1.py
run_check validate_protocol_test python3 MAP_System/tests/test_validate_protocol.py
run_check capability_whitelist_test python3 MAP_System/tests/test_capability_whitelist.py
run_check pre_dispatch_policy_test python3 MAP_System/tests/test_pre_dispatch_policy.py
run_check runner_policy_gate_test MAP_System/.venv/bin/python MAP_System/tests/test_runner_policy_gate.py
run_check mission_control_tui_test python3 MAP_System/tests/test_mission_control_tui.py
run_check durable_execution_test python3 MAP_System/tests/test_durable_execution.py
run_check resilience_controls_test python3 MAP_System/tests/test_resilience_controls.py
run_check chaos_resilience_test python3 MAP_System/tests/test_chaos_resilience.py
run_check command_center_intake_test python3 MAP_System/tests/test_command_center_intake.py
run_check librarian_test python3 MAP_System/tests/test_librarian.py
run_check local_runner_test python3 MAP_System/tests/test_local_runner.py
run_check aider_wrapper_test python3 MAP_System/tests/test_aider_wrapper.py
run_check decomposer_edges_test MAP_System/.venv/bin/python MAP_System/tests/test_decomposer_edges.py
run_check context_summary_drift_test python3 MAP_System/tests/test_context_summary_drift.py
run_check multi_project_isolation_test python3 MAP_System/tests/test_multi_project_isolation.py
run_check integration_test MAP_System/.venv/bin/python MAP_System/scripts/integration_test.py
run_check multigate_regression MAP_System/.venv/bin/python MAP_System/scripts/multigate_regression_test.py

TOTAL=$((PASS + FAIL))
printf 'SUMMARY pass=%s fail=%s total=%s\n' "$PASS" "$FAIL" "$TOTAL"

if [ "$FAIL" -ne 0 ]; then
  exit 1
fi
exit 0
