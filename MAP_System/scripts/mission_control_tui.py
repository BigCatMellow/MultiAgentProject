#!/usr/bin/env python3
"""Read-only mission-control TUI prototype (TASK-160, from mission-control-tui-spec.md).

Aggregates durable MAP state (map.db/task files/workflow/task_graph.json/
events.jsonl/agents/status.json) plus hcom list/events into vitals/roster/
flight-board/attention-queue/event-stream panels. Never a second source of
truth: every function here reads existing state and existing tools
(graph/runner.py, liveness_reaper.py's snapshot) rather than recomputing
routing or liveness logic independently.

This module's data-aggregation layer has no dependency on any TUI/rendering
library and is fully testable on its own. The rendering layer
(`_mission_control_app.py`) uses Python's built-in `curses` module -- the
spec named Textual/k9s-style as the candidate stack, but that would need an
external package install; curses ships an equivalent read-only prototype
today with zero new dependencies. The rendering layer is imported lazily so
the data layer and this module's own tests never require a display/TTY.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.dead_letter_queue import queue_depth  # noqa: E402
from MAP_System.scripts.liveness_reaper import (  # noqa: E402
    build_snapshot as build_liveness_records,
    normalize_hcom_status,
)

VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
RUNNER_PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


def _run_json(cmd: list[str]) -> dict:
    result = subprocess.run(cmd, cwd=REPO, text=True, capture_output=True, check=False)
    if result.returncode not in (0, 1):
        # 1 is a normal "route needs attention" exit for some scripts; only
        # treat other codes as a hard failure the caller must surface.
        raise RuntimeError(f"{' '.join(cmd)} failed: {result.stderr.strip()}")
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{' '.join(cmd)} did not emit valid JSON: {exc}") from exc


def get_runner_snapshot() -> dict:
    """The single source of truth for route/queue state -- read via
    graph/runner.py, never recomputed here.
    """
    return _run_json([RUNNER_PYTHON, str(ROOT / "graph" / "runner.py"), "--pretty"])


def get_vitals(snapshot: dict | None = None) -> dict:
    snapshot = snapshot or get_runner_snapshot()
    return {
        "next_route": snapshot.get("next_route"),
        "ready_count": len(snapshot.get("ready_tasks", [])),
        "submitted_count": len(snapshot.get("submitted_tasks", [])),
        "in_progress_count": len(snapshot.get("in_progress_tasks", [])),
        "blocked_count": len(snapshot.get("blocked_tasks", [])),
        "halt_state": (snapshot.get("halt_state") or {}).get("state", "clear"),
        "available_agents": len(snapshot.get("available_agents", [])),
    }


def get_liveness_snapshot(liveness_md: Path | None = None) -> list[dict]:
    """Parses the markdown table liveness_reaper.py already produces,
    rather than recomputing agent state independently.
    """
    liveness_md = liveness_md or (ROOT / "shared" / "liveness-state.md")
    if not liveness_md.exists():
        return []
    rows = []
    in_table = False
    for line in liveness_md.read_text(encoding="utf-8").splitlines():
        if line.startswith("| Agent | State"):
            in_table = True
            continue
        if in_table:
            if not line.startswith("|"):
                break
            if line.startswith("|---"):
                continue
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) == 5:
                rows.append({
                    "agent_id": cells[0],
                    "state": cells[1],
                    "active_task": cells[2] if cells[2] != "-" else None,
                    "lane": cells[3],
                    "evidence": cells[4],
                })
    return rows


def get_hcom_list_json() -> list[dict] | None:
    """Best-effort live hcom roster read. None means hcom was unavailable
    or emitted invalid JSON; callers should fall back to durable snapshots.
    """
    try:
        result = subprocess.run(
            ["hcom", "list", "--json"],
            cwd=REPO,
            text=True,
            capture_output=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, list) else None


def _liveness_records_to_roster(records) -> list[dict]:
    return [
        {
            "agent_id": record.agent_id,
            "state": record.state,
            "active_task": record.active_task,
            "lane": record.lane,
            "evidence": record.evidence,
        }
        for record in records
    ]


def get_live_liveness_snapshot(
    raw_hcom: list[dict] | dict[str, dict] | None = None,
    status_path: Path | None = None,
    db_path: Path | None = None,
) -> list[dict]:
    """Build a read-only roster from live hcom data through liveness_reaper.

    This composes TASK-177's hcom normalization and TASK-158's liveness
    classifier instead of duplicating liveness rules in mission-control.
    """
    if raw_hcom is None:
        raw_hcom = get_hcom_list_json()
    if raw_hcom is None:
        return []
    hcom_status = normalize_hcom_status(raw_hcom)
    return _liveness_records_to_roster(
        build_liveness_records(
            status_path=status_path or (ROOT / "agents" / "status.json"),
            hcom_status_by_agent=hcom_status,
            db_path=db_path or (ROOT / "map.db"),
        )
    )


def get_roster(liveness_md: Path | None = None, prefer_live: bool = True) -> list[dict]:
    if prefer_live and liveness_md is None:
        live = get_live_liveness_snapshot()
        if live:
            return live
    return get_liveness_snapshot(liveness_md)


def get_flight_board(snapshot: dict | None = None) -> dict:
    snapshot = snapshot or get_runner_snapshot()
    return {
        "ready": snapshot.get("ready_tasks", []),
        "in_progress": snapshot.get("in_progress_tasks", []),
        "submitted": snapshot.get("submitted_tasks", []),
        "blocked": snapshot.get("blocked_tasks", []),
        "dispatch_blocked": snapshot.get("dispatch_blocked_tasks", []),
        "policy_gated": snapshot.get("policy_gated_tasks", []),
        "policy_rejected": snapshot.get("policy_rejected_tasks", []),
    }


def _relative_path_label(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def get_dead_letter_summary(queue_log: Path | None = None) -> dict:
    queue_log = queue_log or (ROOT / "dead_letters" / "dead_letters.jsonl")
    try:
        queued = queue_depth(queue_log=queue_log)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        return {
            "queued": None,
            "queue_log": _relative_path_label(queue_log),
            "error": str(exc),
        }
    return {
        "queued": queued,
        "queue_log": _relative_path_label(queue_log),
        "error": None,
    }


def _policy_detail(snapshot: dict, task_id: str) -> str:
    for result in snapshot.get("policy_results", []):
        if result.get("task_id") != task_id:
            continue
        decision = result.get("decision") or "policy_gate"
        worker = result.get("candidate_worker") or "dispatch"
        reasons = ", ".join(result.get("reasons", [])) or "no reason recorded"
        authority = result.get("approval_authority")
        authority_detail = f"; authority={authority}" if authority else ""
        return f"{decision} via {worker}: {reasons}{authority_detail}"
    return "pre-dispatch policy result present; inspect runner policy_results"


def get_attention_queue(
    snapshot: dict | None = None,
    roster: list[dict] | None = None,
    drift: dict | None = None,
    dead_letter: dict | None = None,
) -> list[dict]:
    """Human-decision-only items: submitted tasks needing review, an
    active halt, policy gates/rejections, drift/dead-letter pressure, and
    broken/suspect agents. Filters out routine chatter, per the spec's
    "only human-decision items" rule.
    """
    snapshot = snapshot or get_runner_snapshot()
    roster = roster if roster is not None else get_roster()
    items = []

    for task_id in snapshot.get("submitted_tasks", []):
        items.append({"kind": "review_needed", "target": task_id, "detail": "awaiting independent review"})

    halt = snapshot.get("halt_state") or {}
    if halt.get("state") != "clear":
        items.append({
            "kind": "halt_active",
            "target": halt.get("target") or "global",
            "detail": f"{halt.get('state')}: {halt.get('reason')}",
        })

    for task_id in snapshot.get("policy_gated_tasks", []):
        items.append({"kind": "policy_gate", "target": task_id, "detail": _policy_detail(snapshot, task_id)})

    for task_id in snapshot.get("policy_rejected_tasks", []):
        items.append({"kind": "policy_rejected", "target": task_id, "detail": _policy_detail(snapshot, task_id)})

    if drift and drift.get("drifted"):
        items.append({"kind": "source_drift", "target": "task_mirrors", "detail": drift.get("detail", "mirror validator failed")})

    if dead_letter:
        if dead_letter.get("error"):
            items.append({"kind": "dead_letter_error", "target": "dead_letter_queue", "detail": dead_letter["error"]})
        elif dead_letter.get("queued", 0) > 0:
            items.append({
                "kind": "dead_letter_queue",
                "target": f"{dead_letter['queued']} queued",
                "detail": dead_letter.get("queue_log", "MAP_System/dead_letters/dead_letters.jsonl"),
            })

    for record in roster:
        if record["state"] in {"broken", "suspect"}:
            items.append({"kind": "agent_attention", "target": record["agent_id"], "detail": f"{record['state']}: {record['evidence']}"})

    return items


def get_event_stream(limit: int = 20, event_log: Path | None = None) -> list[dict]:
    event_log = event_log or (ROOT / "events" / "events.jsonl")
    if not event_log.exists():
        return []
    lines = [l for l in event_log.read_text(encoding="utf-8").splitlines() if l.strip()]
    events = []
    for line in lines[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def get_task_record(task_id: str, task_dir: Path | None = None) -> dict | None:
    task_dir = task_dir or (ROOT / "tasks")
    task_file = task_dir / f"{task_id}.json"
    if not task_file.exists():
        return None
    return json.loads(task_file.read_text(encoding="utf-8"))


def _events_for_task(events: list[dict], task_id: str, limit: int = 5) -> list[dict]:
    return [event for event in events if event.get("task_id") == task_id][-limit:]


def _events_for_sender(events: list[dict], agent_id: str, limit: int = 5) -> list[dict]:
    return [event for event in events if event.get("sender") == agent_id or event.get("actor") == agent_id][-limit:]


def get_task_drilldown(
    task_id: str,
    snapshot: dict | None = None,
    events: list[dict] | None = None,
    task_dir: Path | None = None,
) -> dict:
    snapshot = snapshot or get_runner_snapshot()
    events = events if events is not None else get_event_stream(limit=200)
    board = get_flight_board(snapshot)
    halt = snapshot.get("halt_state") or {}
    policy_results = [
        result for result in snapshot.get("policy_results", [])
        if result.get("task_id") == task_id
    ]
    return {
        "kind": "task",
        "target": task_id,
        "task": get_task_record(task_id, task_dir),
        "queues": [queue for queue, task_ids in board.items() if task_id in task_ids],
        "policy_results": policy_results,
        "halt": halt if halt.get("state") != "clear" and (halt.get("target") in {None, task_id} or halt.get("scope") == "global") else None,
        "recent_events": _events_for_task(events, task_id),
    }


def get_agent_drilldown(
    agent_id: str,
    roster: list[dict] | None = None,
    events: list[dict] | None = None,
) -> dict:
    roster = roster if roster is not None else get_roster()
    events = events if events is not None else get_event_stream(limit=200)
    record = next((item for item in roster if item.get("agent_id") == agent_id), None)
    return {
        "kind": "agent",
        "target": agent_id,
        "record": record,
        "active_task": record.get("active_task") if record else None,
        "recent_events": _events_for_sender(events, agent_id),
    }


def get_attention_drilldown(
    item: dict,
    snapshot: dict | None = None,
    roster: list[dict] | None = None,
    events: list[dict] | None = None,
    drift: dict | None = None,
    dead_letter: dict | None = None,
    task_dir: Path | None = None,
) -> dict:
    snapshot = snapshot or get_runner_snapshot()
    roster = roster if roster is not None else get_roster()
    events = events if events is not None else get_event_stream(limit=200)
    drift = drift if drift is not None else check_source_drift()
    dead_letter = dead_letter if dead_letter is not None else get_dead_letter_summary()

    target = item.get("target")
    detail: dict = {"kind": "attention", "target": target, "item": item}
    if isinstance(target, str) and target.startswith("TASK-"):
        detail["task"] = get_task_drilldown(target, snapshot, events, task_dir)
    elif item.get("kind") == "agent_attention":
        detail["agent"] = get_agent_drilldown(str(target), roster, events)
    elif item.get("kind") == "source_drift":
        detail["drift"] = drift
    elif item.get("kind") in {"dead_letter_queue", "dead_letter_error"}:
        detail["dead_letter"] = dead_letter
    return detail


def check_source_drift() -> dict:
    """The spec's required failure-mode check: on source disagreement
    (e.g. task_graph.json vs map.db mismatch), show a drift warning, not a
    silent/blank panel. Reuses validate_task_mirrors.py rather than
    reimplementing the comparison.
    """
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_task_mirrors.py")],
        cwd=REPO, text=True, capture_output=True, check=False,
    )
    return {
        "drifted": result.returncode != 0,
        "detail": result.stdout.strip() if result.returncode != 0 else "mirrors consistent",
    }


def build_dashboard_snapshot() -> dict:
    """One aggregation call producing everything a render layer needs --
    the read-only contract this whole module exists to enforce.
    """
    snapshot = get_runner_snapshot()
    roster = get_roster()
    drift = check_source_drift()
    dead_letter = get_dead_letter_summary()
    return {
        "runner": snapshot,
        "vitals": get_vitals(snapshot),
        "roster": roster,
        "flight_board": get_flight_board(snapshot),
        "attention_queue": get_attention_queue(snapshot, roster, drift, dead_letter),
        "event_stream": get_event_stream(),
        "drift": drift,
        "dead_letter": dead_letter,
    }


READ_ONLY_KEYBINDINGS = {
    "q": "quit",
    "r": "refresh",
    "/": "filter",
    "tab": "focus_next",
    "shift+tab": "focus_previous",
    "up/down": "move_selection",
    "j/k": "move_selection",
    "enter": "open_drilldown",
    "esc": "close_drilldown_or_clear_filter",
    "t": "task_view",
    "a": "agent_roster",
    "e": "event_stream",
    "!": "attention_queue",
    "?": "help",
}

# Present but disabled/dry-run until the read-only view is proven correct,
# per the spec's explicit non-goal list -- no key here calls a write path.
DISABLED_INTERVENTION_KEYBINDINGS = {
    "A": "approve_selected (disabled: requires read-only validation first)",
    "R": "reject_selected (disabled)",
    "K": "kill_or_suspend_agent (disabled)",
    "N": "resume_nudge_agent (disabled)",
    "B": "bump_budget (disabled)",
    "O": "override_false_halt (disabled)",
    "D": "dead_letter_replay (disabled)",
}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print the aggregated dashboard snapshot as JSON and exit (no TUI)")
    args = parser.parse_args()

    if args.json:
        print(json.dumps(build_dashboard_snapshot(), indent=2))
        return 0

    try:
        from MAP_System.scripts._mission_control_app import run_app  # noqa: E402
    except ModuleNotFoundError as exc:
        print(
            f"Interactive rendering layer unavailable ({exc}). Run with "
            "--json to see the aggregated read-only snapshot instead.",
            file=sys.stderr,
        )
        return 1
    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
