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
run_check validate_task_graph python3 MAP_System/scripts/validate_task_graph.py
run_check promote_task_test python3 MAP_System/tests/test_promote_task.py
run_check no_self_review_test python3 MAP_System/tests/test_no_self_review.py
run_check exporter_hpom_fields_test python3 MAP_System/tests/test_exporter_hpom_fields.py
run_check review_gate_test python3 MAP_System/tests/test_review_gate.py
run_check release_gate_test python3 MAP_System/tests/test_release_gate.py
run_check map_metrics_test python3 MAP_System/tests/test_map_metrics.py
run_check map_metrics_aliases_test python3 MAP_System/tests/test_map_metrics_aliases.py
run_check map_emergence_test python3 MAP_System/tests/test_map_emergence.py
run_check map_task_auto_id_test python3 MAP_System/tests/test_map_task_auto_id.py
run_check map_task_rework_test python3 MAP_System/tests/test_map_task_rework.py
run_check map_emergence_stale_test python3 MAP_System/tests/test_map_emergence_stale.py
run_check validate_task_graph_shared_outputs_test python3 MAP_System/tests/test_validate_task_graph_shared_outputs.py
run_check validate_events_test python3 MAP_System/tests/test_validate_events.py
run_check git_operation_lock_test python3 MAP_System/tests/test_git_operation_lock.py
run_check reconcile_agents_test python3 MAP_System/tests/test_reconcile_agents.py
run_check runner_task_classification_test MAP_System/.venv/bin/python MAP_System/tests/test_runner_task_classification.py
run_check limit_watcher_test python3 MAP_System/tests/test_limit_watcher.py
run_check local_runner_test python3 MAP_System/tests/test_local_runner.py
run_check aider_wrapper_test python3 MAP_System/tests/test_aider_wrapper.py
run_check integration_test MAP_System/.venv/bin/python MAP_System/scripts/integration_test.py
run_check multigate_regression MAP_System/.venv/bin/python MAP_System/scripts/multigate_regression_test.py

TOTAL=$((PASS + FAIL))
printf 'SUMMARY pass=%s fail=%s total=%s\n' "$PASS" "$FAIL" "$TOTAL"

if [ "$FAIL" -ne 0 ]; then
  exit 1
fi
exit 0
