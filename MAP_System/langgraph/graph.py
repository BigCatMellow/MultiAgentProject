"""Starter LangGraph-oriented workflow shape for MAP.

This module intentionally avoids importing LangGraph until TASK-002 installs or
confirms the dependency. The canonical state remains in repository files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import json


ROOT = Path(__file__).resolve().parents[1]
TASK_GRAPH_PATH = ROOT / "workflow" / "task_graph.json"


@dataclass
class WorkflowState:
    project_id: str
    ready_tasks: list[str] = field(default_factory=list)
    blocked_tasks: list[str] = field(default_factory=list)
    submitted_tasks: list[str] = field(default_factory=list)


def load_task_graph(path: Path = TASK_GRAPH_PATH) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def summarize_state(graph: dict) -> WorkflowState:
    tasks = graph.get("tasks", [])
    return WorkflowState(
        project_id=graph["project_id"],
        ready_tasks=[task["task_id"] for task in tasks if task.get("status") == "READY"],
        blocked_tasks=[task["task_id"] for task in tasks if task.get("status") == "BLOCKED"],
        submitted_tasks=[task["task_id"] for task in tasks if task.get("status") == "SUBMITTED"],
    )


def next_route(state: WorkflowState) -> str:
    if state.submitted_tasks:
        return "review"
    if state.ready_tasks:
        return "claim_or_assign"
    return "wait_or_reconcile"


if __name__ == "__main__":
    current = summarize_state(load_task_graph())
    print(
        json.dumps(
            {
                "project_id": current.project_id,
                "ready_tasks": current.ready_tasks,
                "blocked_tasks": current.blocked_tasks,
                "submitted_tasks": current.submitted_tasks,
                "next_route": next_route(current),
            },
            indent=2,
        )
    )

