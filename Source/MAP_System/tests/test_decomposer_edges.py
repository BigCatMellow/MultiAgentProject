#!/usr/bin/env python3
"""Dependency-edge regression tests (taxonomy audit missing test #4, TASK-192).

Covers decomposition/graph dependency-edge cases beyond the trivial 2-node
cycle: multi-node cycles, self-dependency, dangling dependency IDs, and
diamond dependencies with mixed terminal/active states — against both
`validate_task_graph.py` (structural validation) and the runner's
ready-computation (`graph/runner.py:evaluate_tasks`).

Run with MAP_System/.venv/bin/python (the runner imports langgraph).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

SCRIPT = ROOT / "scripts" / "validate_task_graph.py"
spec = importlib.util.spec_from_file_location("validate_task_graph", SCRIPT)
assert spec and spec.loader
vtg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vtg)

from MAP_System.graph.runner import DEPENDENCY_SATISFIED_STATUSES, evaluate_tasks


def graph_task(task_id: str, deps: list[str], status: str = "READY") -> dict:
    return {
        "task_id": task_id,
        "title": f"{task_id} title",
        "task_type": "implementation",
        "role": "implementer",
        "status": status,
        "dependencies": deps,
        "owner": "test-owner",
        "output_paths": [f"MAP_System/out/{task_id}.md"],
        "acceptance_criteria": ["criterion"],
    }


def validate_graph(tasks: list[dict]) -> list[str]:
    """Run vtg.validate with ROOT pointed at a tmpdir holding matching task
    file stubs, so synthetic graphs don't trip the missing-task-file check."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "tasks").mkdir()
        for task in tasks:
            (base / "tasks" / f"{task['task_id']}.json").write_text(
                json.dumps(task), encoding="utf-8"
            )
        original_root = vtg.ROOT
        vtg.ROOT = base
        try:
            return vtg.validate({"project_id": "TEST", "tasks": tasks})
        finally:
            vtg.ROOT = original_root


def runner_task(task_id: str, deps: list[str], status: str = "READY") -> dict:
    return {
        "task_id": task_id,
        "status": status,
        "dependencies": deps,
        "task_type": "review",  # review lane: pre-dispatch allows without halt/policy noise
        "role": "reviewer",
        "title": f"{task_id} title",
        "description": "",
        "acceptance_criteria": [],
    }


def test_three_node_cycle_detected():
    tasks = [
        graph_task("TASK-A", ["TASK-C"]),
        graph_task("TASK-B", ["TASK-A"]),
        graph_task("TASK-C", ["TASK-B"]),
    ]
    errors = validate_graph(tasks)
    assert any("Dependency cycle" in e for e in errors), errors


def test_self_dependency_detected_as_cycle():
    errors = validate_graph([graph_task("TASK-A", ["TASK-A"])])
    assert any("Dependency cycle" in e for e in errors), errors


def test_dangling_dependency_reported_without_crash():
    errors = validate_graph([graph_task("TASK-A", ["TASK-GHOST"])])
    assert any("unknown dependency TASK-GHOST" in e for e in errors), errors
    # a dangling ID must not be misreported as a cycle
    assert not any("Dependency cycle" in e for e in errors), errors


def test_diamond_with_mixed_states_is_valid():
    # D (terminal) <- B (READY), C (IN_PROGRESS); A (READY) <- B, C
    tasks = [
        graph_task("TASK-D", [], status="RELEASED"),
        graph_task("TASK-B", ["TASK-D"], status="READY"),
        graph_task("TASK-C", ["TASK-D"], status="IN_PROGRESS"),
        graph_task("TASK-A", ["TASK-B", "TASK-C"], status="READY"),
    ]
    assert validate_graph(tasks) == []


def test_runner_diamond_ready_computation():
    state = {
        "tasks": [
            runner_task("TASK-D", [], status="RELEASED"),
            runner_task("TASK-B", ["TASK-D"], status="READY"),
            runner_task("TASK-C", ["TASK-D"], status="IN_PROGRESS"),
            runner_task("TASK-A", ["TASK-B", "TASK-C"], status="READY"),
        ],
        "agents": {},
    }
    result = evaluate_tasks(state)
    # B's dependency is terminal -> ready; A waits on active B/C -> blocked
    assert result["ready_tasks"] == ["TASK-B"], result["ready_tasks"]
    assert "TASK-A" in result["blocked_tasks"], result["blocked_tasks"]
    assert result["in_progress_tasks"] == ["TASK-C"]


def test_runner_retired_dependency_does_not_satisfy():
    # TASK-100 semantics: RETIRED is terminal-by-decision and must never
    # satisfy another task's dependency expectation of completed output.
    assert "RETIRED" not in DEPENDENCY_SATISFIED_STATUSES
    state = {
        "tasks": [
            runner_task("TASK-R", [], status="RETIRED"),
            runner_task("TASK-A", ["TASK-R"], status="READY"),
        ],
        "agents": {},
    }
    result = evaluate_tasks(state)
    assert result["ready_tasks"] == [], result["ready_tasks"]
    assert "TASK-A" in result["blocked_tasks"], result["blocked_tasks"]


def test_runner_self_dependency_never_ready():
    state = {"tasks": [runner_task("TASK-A", ["TASK-A"], status="READY")],
             "agents": {}}
    result = evaluate_tasks(state)
    assert result["ready_tasks"] == [], result["ready_tasks"]
    assert "TASK-A" in result["blocked_tasks"], result["blocked_tasks"]


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    print(f"{len(tests)} decomposer-edge tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
