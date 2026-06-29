#!/usr/bin/env python3
"""Executable LangGraph runner for the file-backed MAP workflow."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from typing import Any, Literal, TypedDict

import yaml
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt


ROOT = Path(__file__).resolve().parents[1]
TASK_GRAPH_PATH = ROOT / "workflow" / "task_graph.json"
RUNTIME_POLICY_PATH = ROOT / "workflow" / "runtime_policy.yaml"
MAP_DB_PATH = ROOT / "map.db"

Route = Literal[
    "review",
    "wait_for_agent",
    "propose_helper",
    "claim_or_assign",
    "wait_or_reconcile",
]


class MapState(TypedDict, total=False):
    graph_path: str
    db_path: str
    state_source: str
    pending_gates: list[dict[str, Any]]  # all pending approval gates when interrupted
    gate_decision: bool | None           # True=approved, False=rejected, None=pending
    runtime_policy_path: str
    project_id: str
    runtime_policy: dict[str, Any]
    helper_policy: dict[str, Any]
    agent_status_path: str
    agents: dict[str, dict[str, Any]]
    available_agents: list[str]
    unavailable_agents: list[str]
    tasks: list[dict[str, Any]]
    done_task_ids: list[str]
    in_progress_tasks: list[str]
    submitted_tasks: list[str]
    ready_tasks: list[str]
    blocked_tasks: list[str]
    ready_tasks_waiting_for_agent: list[str]
    helper_candidate_tasks: list[str]
    helper_notes: list[dict[str, Any]]
    active_helper_notes: list[str]
    max_active_helpers: int
    recommended_action: str
    command_hint: str
    next_route: Route
    events: list[str]


def project_relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def load_task_graph(state: MapState) -> MapState:
    graph_path = Path(state.get("graph_path") or TASK_GRAPH_PATH)
    db_path = Path(state.get("db_path") or MAP_DB_PATH)
    if db_path.exists():
        project_id, tasks = load_tasks_from_sqlite(db_path)
        return {
            **state,
            "graph_path": str(graph_path),
            "db_path": str(db_path),
            "state_source": "sqlite",
            "project_id": project_id,
            "tasks": tasks,
            "events": [*state.get("events", []), f"loaded tasks from {project_relative(db_path)}"],
        }

    with graph_path.open("r", encoding="utf-8") as handle:
        graph = json.load(handle)

    return {
        **state,
        "graph_path": str(graph_path),
        "db_path": str(db_path),
        "state_source": "json",
        "project_id": graph["project_id"],
        "tasks": graph.get("tasks", []),
        "events": [*state.get("events", []), f"loaded {graph_path}"],
    }


def load_tasks_from_sqlite(db_path: Path) -> tuple[str, list[dict[str, Any]]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        task_rows = conn.execute(
            """
            SELECT task_id, project_id, title, description, task_type, role, status,
                   priority, required_agent, owner, claimed_by, lease_expires_at,
                   heartbeat_at, attempt, max_attempts, created_at, updated_at
            FROM tasks
            ORDER BY task_id
            """
        ).fetchall()
        dependencies = load_task_multi_values(
            conn,
            "SELECT task_id, depends_on AS value FROM task_dependencies ORDER BY task_id, depends_on",
        )
        output_paths = load_task_multi_values(
            conn,
            "SELECT task_id, path AS value FROM task_output_paths ORDER BY task_id, path",
        )
        acceptance_criteria = load_task_multi_values(
            conn,
            "SELECT task_id, criterion AS value FROM task_acceptance_criteria ORDER BY task_id, id",
        )

    tasks: list[dict[str, Any]] = []
    for row in task_rows:
        task = dict(row)
        task["dependencies"] = dependencies.get(row["task_id"], [])
        task["output_paths"] = output_paths.get(row["task_id"], [])
        task["acceptance_criteria"] = acceptance_criteria.get(row["task_id"], [])
        tasks.append(task)

    project_id = task_rows[0]["project_id"] if task_rows else "unknown"
    return project_id, tasks


def load_task_multi_values(conn: sqlite3.Connection, sql: str) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for row in conn.execute(sql):
        values.setdefault(row["task_id"], []).append(row["value"])
    return values


def load_runtime_policy(state: MapState) -> MapState:
    policy_path = Path(state.get("runtime_policy_path") or RUNTIME_POLICY_PATH)
    with policy_path.open("r", encoding="utf-8") as handle:
        policy = yaml.safe_load(handle) or {}

    runtime_policy = policy.get("runtime_policy", {})
    helper_policy = runtime_policy.get("helper_agents", {})

    return {
        **state,
        "runtime_policy_path": str(policy_path),
        "runtime_policy": runtime_policy,
        "helper_policy": helper_policy,
        "max_active_helpers": int(helper_policy.get("maximum_active_helpers", 0) or 0),
        "events": [
            *state.get("events", []),
            f"loaded {project_relative(policy_path)}",
        ],
    }


def load_agent_status(state: MapState) -> MapState:
    runtime_policy = state.get("runtime_policy", {})
    status_path = ROOT / runtime_policy.get("agent_status_path", "agents/status.json")
    db_path = Path(state.get("db_path") or MAP_DB_PATH)
    if state.get("state_source") == "sqlite" and db_path.exists():
        agents = load_agents_from_sqlite(db_path)
        source_event = f"loaded agents from {project_relative(db_path)}"
    elif status_path.exists():
        with status_path.open("r", encoding="utf-8") as handle:
            status_data = json.load(handle)
        agents = status_data.get("agents", {})
        source_event = f"loaded {project_relative(status_path)}"
    else:
        agents = {}
        source_event = f"loaded {project_relative(status_path)}"

    available_agents = sorted(
        agent_id
        for agent_id, details in agents.items()
        if details.get("status") == "available" and is_assignable_agent(agent_id, details)
    )
    unavailable_agents = sorted(
        agent_id
        for agent_id, details in agents.items()
        if details.get("status") in {"busy", "standby", "offline"}
        and is_assignable_agent(agent_id, details)
    )

    return {
        **state,
        "agent_status_path": str(status_path),
        "agents": agents,
        "available_agents": available_agents,
        "unavailable_agents": unavailable_agents,
        "events": [
            *state.get("events", []),
            source_event,
        ],
    }


def is_assignable_agent(agent_id: str, details: dict[str, Any]) -> bool:
    if details.get("agent_type") == "system":
        return False
    return agent_id not in {"command-center", "langgraph-runner"}


def load_agents_from_sqlite(db_path: Path) -> dict[str, dict[str, Any]]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            """
            SELECT agent_id, label, agent_type, helper_tag, status, reason,
                   resume_after, last_heartbeat, created_at, updated_at
            FROM agents
            ORDER BY agent_id
            """
        ).fetchall()
    return {row["agent_id"]: dict(row) for row in rows}


def read_helper_note_metadata(path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "tag": path.stem,
        "path": project_relative(path),
        "status": "unknown",
    }

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("- ") or ":" not in stripped:
            continue
        key, value = stripped[2:].split(":", 1)
        normalized_key = key.strip().replace(" ", "_")
        metadata[normalized_key] = value.strip()

    return metadata


def scan_helper_notes(state: MapState) -> MapState:
    helper_policy = state.get("helper_policy", {})
    notes_dir = ROOT / helper_policy.get("notes_dir", "inbox/helpers")
    note_paths = sorted(notes_dir.glob("helper-*.md")) if notes_dir.exists() else []
    helper_notes = [read_helper_note_metadata(path) for path in note_paths]
    active_helper_notes = [
        note["tag"]
        for note in helper_notes
        if str(note.get("status", "")).lower() in {"active", "running", "in_progress"}
    ]

    return {
        **state,
        "helper_notes": helper_notes,
        "active_helper_notes": active_helper_notes,
        "events": [
            *state.get("events", []),
            f"scanned {len(helper_notes)} helper notes",
        ],
    }


def evaluate_tasks(state: MapState) -> MapState:
    tasks = state.get("tasks", [])
    done_task_ids = {
        task["task_id"]
        for task in tasks
        if task.get("status") in {"DONE", "APPROVED"}
    }

    in_progress_tasks: list[str] = []
    ready_tasks: list[str] = []
    blocked_tasks: list[str] = []
    submitted_tasks: list[str] = []
    ready_tasks_waiting_for_agent: list[str] = []
    helper_candidate_tasks: list[str] = []

    for task in tasks:
        task_id = task["task_id"]
        status = task.get("status")

        if status in {"IN_PROGRESS", "CLAIMED"}:
            in_progress_tasks.append(task_id)
            continue

        if status == "SUBMITTED":
            submitted_tasks.append(task_id)
            continue

        dependencies = task.get("dependencies", [])
        dependencies_satisfied = all(
            dependency in done_task_ids for dependency in dependencies
        )

        if status == "READY" and dependencies_satisfied:
            if task_requires_unavailable_agent(task, state):
                ready_tasks_waiting_for_agent.append(task_id)
                continue
            ready_tasks.append(task_id)
            if task_would_benefit_from_helper(task):
                helper_candidate_tasks.append(task_id)
        elif status == "BLOCKED" and dependencies_satisfied:
            if task_requires_unavailable_agent(task, state):
                ready_tasks_waiting_for_agent.append(task_id)
                continue
            ready_tasks.append(task_id)
            if task_would_benefit_from_helper(task):
                helper_candidate_tasks.append(task_id)
        elif status in {"READY", "BLOCKED"}:
            blocked_tasks.append(task_id)

    return {
        **state,
        "done_task_ids": sorted(done_task_ids),
        "in_progress_tasks": in_progress_tasks,
        "ready_tasks": ready_tasks,
        "blocked_tasks": blocked_tasks,
        "submitted_tasks": submitted_tasks,
        "ready_tasks_waiting_for_agent": ready_tasks_waiting_for_agent,
        "helper_candidate_tasks": helper_candidate_tasks,
        "events": [
            *state.get("events", []),
            f"evaluated {len(tasks)} tasks",
        ],
    }


def task_requires_unavailable_agent(task: dict[str, Any], state: MapState) -> bool:
    required_agent = task.get("required_agent")
    if not required_agent:
        return False
    return required_agent in set(state.get("unavailable_agents", []))


def task_would_benefit_from_helper(task: dict[str, Any]) -> bool:
    task_type = str(task.get("task_type", "")).lower()
    role = str(task.get("role", "")).lower()
    text = " ".join(
        str(value).lower()
        for value in [
            task.get("title", ""),
            task.get("description", ""),
            " ".join(task.get("acceptance_criteria", [])),
        ]
    )

    if task_type in {"review", "research", "architecture"}:
        return True
    if role in {"reviewer", "researcher", "architect"}:
        return True
    return any(keyword in text for keyword in ["research", "review", "compare", "investigate"])


def should_propose_helper(state: MapState) -> bool:
    helper_policy = state.get("helper_policy", {})
    if not helper_policy.get("enabled", False):
        return False
    if not state.get("helper_candidate_tasks"):
        return False

    max_active_helpers = state.get("max_active_helpers", 0)
    if max_active_helpers <= 0:
        return False
    return len(state.get("active_helper_notes", [])) < max_active_helpers


def choose_route(state: MapState) -> Route:
    if state.get("submitted_tasks"):
        return "review"
    if state.get("ready_tasks_waiting_for_agent") and not state.get("ready_tasks"):
        return "wait_for_agent"
    if should_propose_helper(state):
        return "propose_helper"
    if state.get("ready_tasks"):
        return "claim_or_assign"
    return "wait_or_reconcile"


def route_review(state: MapState) -> MapState:
    return {
        **state,
        "next_route": "review",
        "recommended_action": "Send submitted tasks to an independent reviewer.",
        "command_hint": "ai route --record-event after assigning the review",
        "events": [*state.get("events", []), "routed submitted tasks to review"],
    }


def route_wait_for_agent(state: MapState) -> MapState:
    task_id = state.get("ready_tasks_waiting_for_agent", ["ready-task"])[0]
    task = next(
        (task for task in state.get("tasks", []) if task.get("task_id") == task_id),
        {},
    )
    required_agent = task.get("required_agent", "required agent")
    details = state.get("agents", {}).get(required_agent, {})
    resume_after = details.get("resume_after") or "unknown"
    return {
        **state,
        "next_route": "wait_for_agent",
        "recommended_action": (
            f"{task_id} requires unavailable agent {required_agent}; queue notes "
            f"and continue other work when possible."
        ),
        "command_hint": (
            f'ai agent standby {required_agent} "{details.get("reason") or "unavailable"}" '
            f'"{resume_after}"'
        ),
        "events": [
            *state.get("events", []),
            f"waiting for unavailable agent {required_agent} for {task_id}",
        ],
    }


def route_propose_helper(state: MapState) -> MapState:
    task_id = state.get("helper_candidate_tasks", ["ready-task"])[0]
    slug = task_id.lower().replace("_", "-")
    return {
        **state,
        "next_route": "propose_helper",
        "recommended_action": (
            f"Consider opening a temporary helper for {task_id}; keep a core agent "
            "accountable for integration."
        ),
        "command_hint": (
            f'ai helper start codex {slug} "Assist with {task_id}; read the task file, '
            'keep MAP_System/inbox/helpers/ updated, and report findings."'
        ),
        "events": [*state.get("events", []), f"proposed helper for {task_id}"],
    }


def route_claim_or_assign(state: MapState) -> MapState:
    task_id = state.get("ready_tasks", ["ready-task"])[0]
    return {
        **state,
        "next_route": "claim_or_assign",
        "recommended_action": f"Have one core agent claim or assign {task_id}.",
        "command_hint": "Update the task owner/status in MAP_System/tasks/ and workflow/task_graph.json.",
        "events": [*state.get("events", []), "routed ready tasks to claim_or_assign"],
    }


def route_wait_or_reconcile(state: MapState) -> MapState:
    return {
        **state,
        "next_route": "wait_or_reconcile",
        "recommended_action": "No dependency-satisfied ready work found; reconcile stale claims or wait.",
        "command_hint": "ai status && ai helper list",
        "events": [*state.get("events", []), "routed workflow to wait_or_reconcile"],
    }


def load_approval_gates(db_path: Path) -> list[dict[str, Any]]:
    """Load pending approval gates from SQLite (or empty list if unavailable)."""
    if not db_path.exists():
        return []
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [
                dict(row)
                for row in conn.execute(
                    "SELECT gate_id, name, required_after_task, status FROM approval_gates WHERE status='pending'"
                )
            ]
    except sqlite3.OperationalError:
        return []


def load_all_approval_gates(db_path: Path) -> list[dict[str, Any]]:
    """Load ALL approval gates (any status) in stable insertion order."""
    if not db_path.exists():
        return []
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            return [
                dict(row)
                for row in conn.execute(
                    "SELECT gate_id, name, required_after_task, status FROM approval_gates ORDER BY rowid"
                )
            ]
    except sqlite3.OperationalError:
        return []


def check_approval_gates(state: MapState) -> MapState:
    """Process each pending approval gate in sequence, one interrupt per gate.

    Iterates over ALL gates (including already-resolved ones) in stable order so
    that LangGraph's sequential interrupt positions stay consistent across
    re-executions. Already-resolved gates return their stored resume value
    immediately; only the next unresolved gate actually pauses. This ensures that
    --reject on gate N is applied to interrupt position N, not position 1.
    """
    db_path = Path(state.get("db_path") or MAP_DB_PATH)
    all_gates = load_all_approval_gates(db_path)
    pending_gates = [g for g in all_gates if g["status"] == "pending"]

    if not pending_gates:
        return {**state, "pending_gates": [], "gate_decision": None}

    last_approved: bool | None = None
    for gate in all_gates:
        still_pending = [g for g in all_gates if g["status"] == "pending"]
        decision = interrupt(
            {
                "pending_gates": [
                    {
                        "gate_id": g["gate_id"],
                        "name": g["name"],
                        "required_after_task": g["required_after_task"],
                    }
                    for g in still_pending
                ],
                "message": (
                    f"{len(still_pending)} gate(s) pending. "
                    f"Next: '{gate['name']}'. "
                    "Run with --approve <gate_id> --thread-id <thread> "
                    "or --reject <gate_id> --thread-id <thread>."
                ),
            }
        )
        if gate["status"] == "pending" and decision is not None and db_path.exists():
            approved = (
                bool(decision.get("approved", True))
                if isinstance(decision, dict)
                else bool(decision)
            )
            _record_gate_decision(db_path, gate["gate_id"], approved=approved)
            # Refresh gate status so subsequent iterations see updated state
            gate["status"] = "approved" if approved else "rejected"
            last_approved = approved

    return {**state, "pending_gates": pending_gates, "gate_decision": last_approved}


def _record_gate_decision(db_path: Path, gate_id: str, *, approved: bool) -> None:
    status = "approved" if approved else "rejected"
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE approval_gates SET status=?, approved_at=datetime('now') WHERE gate_id=?",
            (status, gate_id),
        )


def build_graph(*, checkpointer=None):
    graph = StateGraph(MapState)
    graph.add_node("load_task_graph", load_task_graph)
    graph.add_node("load_runtime_policy", load_runtime_policy)
    graph.add_node("load_agent_status", load_agent_status)
    graph.add_node("scan_helper_notes", scan_helper_notes)
    graph.add_node("evaluate_tasks", evaluate_tasks)
    graph.add_node("check_approval_gates", check_approval_gates)
    graph.add_node("review", route_review)
    graph.add_node("wait_for_agent", route_wait_for_agent)
    graph.add_node("propose_helper", route_propose_helper)
    graph.add_node("claim_or_assign", route_claim_or_assign)
    graph.add_node("wait_or_reconcile", route_wait_or_reconcile)

    graph.add_edge(START, "load_task_graph")
    graph.add_edge("load_task_graph", "load_runtime_policy")
    graph.add_edge("load_runtime_policy", "load_agent_status")
    graph.add_edge("load_agent_status", "scan_helper_notes")
    graph.add_edge("scan_helper_notes", "evaluate_tasks")
    graph.add_edge("evaluate_tasks", "check_approval_gates")
    graph.add_conditional_edges(
        "check_approval_gates",
        choose_route,
        {
            "review": "review",
            "wait_for_agent": "wait_for_agent",
            "propose_helper": "propose_helper",
            "claim_or_assign": "claim_or_assign",
            "wait_or_reconcile": "wait_or_reconcile",
        },
    )
    graph.add_edge("review", END)
    graph.add_edge("wait_for_agent", END)
    graph.add_edge("propose_helper", END)
    graph.add_edge("claim_or_assign", END)
    graph.add_edge("wait_or_reconcile", END)
    return graph.compile(checkpointer=checkpointer)


def append_event(state: MapState) -> Path:
    runtime_policy = state.get("runtime_policy", {})
    event_path = ROOT / runtime_policy.get("event_log", "events/events.jsonl")
    event_path.parent.mkdir(parents=True, exist_ok=True)
    created_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    payload = {
        "created_at": created_at,
        "type": "PROGRESS",
        "task_id": None,
        "sender": "langgraph-runner",
        "summary": (
            f"Routed workflow to {state.get('next_route')}: "
            f"{state.get('recommended_action', '')}"
        ),
        "artifact_paths": [
            project_relative(Path(state.get("graph_path", TASK_GRAPH_PATH))),
            project_relative(Path(state.get("runtime_policy_path", RUNTIME_POLICY_PATH))),
        ],
    }
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")
    db_path = Path(state.get("db_path") or MAP_DB_PATH)
    if db_path.exists():
        append_sqlite_event(db_path, payload)
    return event_path


def append_sqlite_event(db_path: Path, payload: dict[str, Any]) -> None:
    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            INSERT OR IGNORE INTO agents (agent_id, label, agent_type, status)
            VALUES (?, ?, ?, ?)
            """,
            ("langgraph-runner", "Langgraph Runner", "system", "available"),
        )
        conn.execute(
            """
            INSERT INTO events
                (event_type, task_id, sender_id, summary, artifact_paths, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.get("type") or "PROGRESS",
                payload.get("task_id"),
                payload.get("sender"),
                payload.get("summary") or "",
                json.dumps(payload.get("artifact_paths", []), sort_keys=True),
                payload.get("created_at"),
            ),
        )


def summarize(state: MapState) -> dict[str, Any]:
    return {
        "project_id": state.get("project_id"),
        "next_route": state.get("next_route"),
        "recommended_action": state.get("recommended_action"),
        "command_hint": state.get("command_hint"),
        "ready_tasks": state.get("ready_tasks", []),
        "ready_tasks_waiting_for_agent": state.get("ready_tasks_waiting_for_agent", []),
        "blocked_tasks": state.get("blocked_tasks", []),
        "submitted_tasks": state.get("submitted_tasks", []),
        "in_progress_tasks": state.get("in_progress_tasks", []),
        "available_agents": state.get("available_agents", []),
        "unavailable_agents": state.get("unavailable_agents", []),
        "helper_candidate_tasks": state.get("helper_candidate_tasks", []),
        "active_helper_notes": state.get("active_helper_notes", []),
        "helper_capacity": {
            "active": len(state.get("active_helper_notes", [])),
            "maximum": state.get("max_active_helpers", 0),
        },
        "done_task_ids": state.get("done_task_ids", []),
        "events": state.get("events", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the MAP LangGraph workflow.")
    parser.add_argument("--graph-path", default=str(TASK_GRAPH_PATH))
    parser.add_argument("--runtime-policy-path", default=str(RUNTIME_POLICY_PATH))
    parser.add_argument("--db", default=str(MAP_DB_PATH), help="Path to map.db")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--record-event", action="store_true")
    parser.add_argument(
        "--thread-id",
        default=None,
        help="Enable checkpointing for this thread (required for --approve/--reject)",
    )
    resume_group = parser.add_mutually_exclusive_group()
    resume_group.add_argument(
        "--approve", metavar="GATE_ID",
        help="Resume an interrupted approval gate with approval (use --thread-id for the checkpoint thread)",
    )
    resume_group.add_argument(
        "--reject", metavar="GATE_ID",
        help="Resume an interrupted approval gate with rejection (use --thread-id for the checkpoint thread)",
    )
    args = parser.parse_args()

    thread_id = args.thread_id

    checkpointer = None
    if thread_id:
        import sys as _sys
        _sys.path.insert(0, str(ROOT.parent))
        from MAP_System.db.checkpointer import MapSqliteSaver  # noqa: E402
        checkpointer = MapSqliteSaver(MAP_DB_PATH)

    app = build_graph(checkpointer=checkpointer)
    cfg = {"configurable": {"thread_id": thread_id}} if thread_id else {}

    if args.approve or args.reject:
        if not thread_id:
            print("error: --thread-id is required with --approve/--reject", file=__import__("sys").stderr)
            return 1
        gate_id = args.approve or args.reject
        approved = bool(args.approve)
        result = app.invoke(Command(resume={"gate_id": gate_id, "approved": approved}), cfg)
        verdict = "approved" if approved else "rejected"

        # If more gates remain the graph re-interrupts; surface that naturally.
        interrupts = result.get("__interrupt__", [])
        if interrupts:
            gate_info = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]
            print(json.dumps(
                {
                    "processed": {"gate_id": gate_id, "decision": verdict},
                    "interrupted": True,
                    "thread_id": thread_id,
                    "gate": gate_info,
                    "resume_hint": (
                        f"langgraph-run --approve <gate_id> --thread-id {thread_id}  # to approve\n"
                        f"langgraph-run --reject <gate_id> --thread-id {thread_id}   # to reject"
                    ),
                },
                indent=2 if args.pretty else None,
            ))
            return 0

        print(json.dumps(
            {"resumed": True, "gate_id": gate_id, "decision": verdict, **summarize(result)},
            indent=2 if args.pretty else None,
        ))
        return 0

    result = app.invoke(
        {
            "graph_path": args.graph_path,
            "runtime_policy_path": args.runtime_policy_path,
            "db_path": args.db,
            "events": [],
        },
        cfg,
    )

    # Detect interrupt (approval gate pause)
    interrupts = result.get("__interrupt__", [])
    if interrupts:
        gate_info = interrupts[0].value if hasattr(interrupts[0], "value") else interrupts[0]
        print(json.dumps(
            {
                "interrupted": True,
                "thread_id": thread_id,
                "gate": gate_info,
                "resume_hint": (
                    f"langgraph-run --approve <gate_id> --thread-id {thread_id}  # to approve\n"
                    f"langgraph-run --reject <gate_id> --thread-id {thread_id}   # to reject"
                ),
            },
            indent=2 if args.pretty else None,
        ))
        return 0

    if args.record_event:
        event_path = append_event(result)
        result["events"] = [
            *result.get("events", []),
            f"recorded route event in {project_relative(event_path)}",
        ]
    print(json.dumps(summarize(result), indent=2 if args.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
