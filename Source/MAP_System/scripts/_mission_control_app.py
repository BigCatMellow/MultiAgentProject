#!/usr/bin/env python3
"""Read-only mission-control TUI rendering layer (TASK-160).

Uses Python's built-in `curses` module -- no external package required.
`textual` was considered (per mission-control-tui-spec.md's candidate
stack) but installing it needed operator approval per this session's
working agreement (ask before external downloads); this curses-based
renderer ships the first working prototype without waiting on that,
while remaining swappable for a Textual app later if the operator wants
the nicer stack -- this module's only job is to RENDER
`build_dashboard_snapshot()`'s dicts; it must never compute liveness,
routing, or drift logic itself.
"""

from __future__ import annotations

import curses
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.mission_control_tui import (  # noqa: E402
    build_dashboard_snapshot,
    get_agent_drilldown,
    get_attention_drilldown,
    get_task_drilldown,
    READ_ONLY_KEYBINDINGS,
    DISABLED_INTERVENTION_KEYBINDINGS,
)

REFRESH_SECONDS = 5
PANELS = ("attention", "tasks", "agents", "events")


def render_vitals_line(vitals: dict) -> str:
    return (
        f"route={vitals['next_route']} ready={vitals['ready_count']} "
        f"in-progress={vitals['in_progress_count']} submitted={vitals['submitted_count']} "
        f"blocked={vitals['blocked_count']} halt={vitals['halt_state']} "
        f"agents={vitals['available_agents']}"
    )


def render_roster_lines(roster: list[dict], max_rows: int, selected: int | None = None) -> list[str]:
    dot = {"working": "*", "alive": "*", "idle": "o", "blocked": "o", "suspect": "?", "broken": "X", "standby": "-"}
    lines = []
    for idx, r in enumerate(roster[:max_rows]):
        marker = ">" if selected == idx else " "
        lines.append(f"{marker}[{dot.get(r['state'], '?')}] {r['agent_id']:<22} {r['state']:<9} {r['active_task'] or '-'}")
    return lines


def flight_board_items(board: dict) -> list[dict]:
    items = []
    for label, key in (
        ("READY", "ready"),
        ("IN-PROGRESS", "in_progress"),
        ("SUBMITTED", "submitted"),
        ("BLOCKED", "blocked"),
        ("DISPATCH-BLK", "dispatch_blocked"),
        ("POLICY-GATE", "policy_gated"),
        ("POLICY-REJ", "policy_rejected"),
    ):
        for task_id in board.get(key, []):
            items.append({"label": label, "task_id": task_id})
    return items


def render_flight_board_lines(board: dict, max_rows: int, selected: int | None = None) -> list[str]:
    lines = []
    for idx, item in enumerate(flight_board_items(board)[:max_rows]):
        marker = ">" if selected == idx else " "
        lines.append(f"{marker}{item['label']:<12} {item['task_id']}")
    return lines[:max_rows]


def render_attention_lines(items: list[dict], max_rows: int, selected: int | None = None) -> list[str]:
    lines = []
    for idx, item in enumerate(items[:max_rows]):
        marker = ">" if selected == idx else " "
        lines.append(f"{marker}! {item['kind']:<16} {item['target']:<20} {item['detail']}")
    return lines


def render_event_lines(events: list[dict], max_rows: int, selected: int | None = None) -> list[str]:
    lines = []
    for idx, event in enumerate(events[-max_rows:]):
        marker = ">" if selected == idx else " "
        trace_id = event.get("trace_id") or "-"
        lines.append(
            f"{marker}{event.get('created_at','?')} {event.get('type','?'):<12} "
            f"{event.get('task_id','-'):<10} trace={trace_id:<16} {event.get('summary','')[:60]}"
        )
    return lines


def render_drilldown_lines(detail: dict, max_rows: int) -> list[str]:
    lines = [f"{detail.get('kind', 'detail').upper()}: {detail.get('target', '-')}"]
    if detail.get("kind") == "task":
        task = detail.get("task") or {}
        lines.extend([
            f"title: {task.get('title', '(task file not found)')}",
            f"status: {task.get('status', '-')}",
            f"owner: {task.get('owner', '-')} claimed_by: {task.get('claimed_by', '-')}",
            f"queues: {', '.join(detail.get('queues', [])) or '-'}",
        ])
        for result in detail.get("policy_results", []):
            reasons = ", ".join(result.get("reasons", [])) or "-"
            lines.append(f"policy: {result.get('decision', '-')} via {result.get('candidate_worker', '-')} {reasons}")
        if detail.get("halt"):
            halt = detail["halt"]
            lines.append(f"halt: {halt.get('state')} {halt.get('reason')}")
        for event in detail.get("recent_events", []):
            lines.append(
                f"event: {event.get('created_at', '?')} {event.get('type', '?')} "
                f"trace={event.get('trace_id') or '-'} {event.get('summary', '')[:80]}"
            )
    elif detail.get("kind") == "agent":
        record = detail.get("record") or {}
        lines.extend([
            f"state: {record.get('state', '(agent not found)')}",
            f"active_task: {detail.get('active_task') or '-'}",
            f"lane: {record.get('lane', '-')}",
            f"evidence: {record.get('evidence', '-')}",
        ])
        for event in detail.get("recent_events", []):
            lines.append(
                f"event: {event.get('created_at', '?')} {event.get('type', '?')} "
                f"{event.get('task_id', '-')} trace={event.get('trace_id') or '-'}"
            )
    elif detail.get("kind") == "attention":
        item = detail.get("item") or {}
        lines.extend([f"attention_kind: {item.get('kind', '-')}", f"detail: {item.get('detail', '-')}"])
        if "task" in detail:
            lines.extend(render_drilldown_lines(detail["task"], max_rows=max_rows)[1:])
        if "agent" in detail:
            lines.extend(render_drilldown_lines(detail["agent"], max_rows=max_rows)[1:])
        if "drift" in detail:
            drift = detail["drift"]
            lines.append(f"drifted: {drift.get('drifted')} {drift.get('detail', '')}")
        if "dead_letter" in detail:
            dead_letter = detail["dead_letter"]
            lines.append(f"dead_letter: queued={dead_letter.get('queued')} error={dead_letter.get('error')}")
    elif detail.get("kind") == "event":
        event = detail.get("event") or {}
        lines.extend([
            f"created_at: {event.get('created_at', '-')}",
            f"type: {event.get('type', '-')}",
            f"task_id: {event.get('task_id', '-')}",
            f"trace_id: {event.get('trace_id', '-')}",
            f"sender: {event.get('sender', event.get('actor', '-'))}",
            f"summary: {event.get('summary', '-')}",
        ])
    return lines[:max_rows]


def _panel_counts(snapshot: dict) -> dict[str, int]:
    return {
        "attention": len(snapshot["attention_queue"]),
        "tasks": len(flight_board_items(snapshot["flight_board"])),
        "agents": len(snapshot["roster"]),
        "events": min(len(snapshot["event_stream"]), 6),
    }


def _bounded_selection(selection: dict[str, int], snapshot: dict) -> dict[str, int]:
    counts = _panel_counts(snapshot)
    bounded = dict(selection)
    for panel, count in counts.items():
        bounded[panel] = min(max(0, bounded.get(panel, 0)), max(0, count - 1))
    return bounded


def selected_drilldown(snapshot: dict, active_panel: str, selection: dict[str, int]) -> dict | None:
    selection = _bounded_selection(selection, snapshot)
    if active_panel == "attention" and snapshot["attention_queue"]:
        item = snapshot["attention_queue"][selection["attention"]]
        return get_attention_drilldown(
            item,
            snapshot=snapshot.get("runner", {}),
            roster=snapshot["roster"],
            events=snapshot["event_stream"],
            drift=snapshot["drift"],
            dead_letter=snapshot["dead_letter"],
        )
    if active_panel == "tasks":
        items = flight_board_items(snapshot["flight_board"])
        if items:
            return get_task_drilldown(items[selection["tasks"]]["task_id"], snapshot.get("runner", {}), snapshot["event_stream"])
    if active_panel == "agents" and snapshot["roster"]:
        return get_agent_drilldown(snapshot["roster"][selection["agents"]]["agent_id"], snapshot["roster"], snapshot["event_stream"])
    if active_panel == "events" and snapshot["event_stream"]:
        event = snapshot["event_stream"][-min(len(snapshot["event_stream"]), 6):][selection["events"]]
        return {"kind": "event", "target": event.get("task_id") or event.get("type"), "event": event}
    return None


def draw(stdscr, snapshot: dict, active_panel: str = "attention", selection: dict[str, int] | None = None) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    row = 0
    selection = _bounded_selection(selection or {}, snapshot)

    def put(text: str) -> None:
        nonlocal row
        if row < height - 1:
            stdscr.addnstr(row, 0, text, max(0, width - 1))
            row += 1

    put(f"MAP Mission Control (read-only)  --  focus={active_panel}; enter drilldown; esc closes detail; q quits")
    put(render_vitals_line(snapshot["vitals"]))
    if snapshot["drift"]["drifted"]:
        put(f"!! MIRROR DRIFT: {snapshot['drift']['detail']}")
    dead_letter = snapshot.get("dead_letter") or {}
    if dead_letter.get("error"):
        put(f"!! DEAD LETTER QUEUE UNREADABLE: {dead_letter['error']}")
    elif dead_letter.get("queued", 0) > 0:
        put(f"!! DEAD LETTER QUEUE: {dead_letter['queued']} queued ({dead_letter.get('queue_log', '-')})")
    put("-" * min(width - 1, 78))

    put("ATTENTION QUEUE:")
    attention_lines = render_attention_lines(snapshot["attention_queue"], 5, selection["attention"] if active_panel == "attention" else None)
    if not attention_lines:
        put("  (none)")
    for line in attention_lines:
        put("  " + line)
    put("-" * min(width - 1, 78))

    put("ROSTER:")
    for line in render_roster_lines(snapshot["roster"], 8, selection["agents"] if active_panel == "agents" else None):
        put("  " + line)
    put("-" * min(width - 1, 78))

    put("FLIGHT BOARD:")
    for line in render_flight_board_lines(snapshot["flight_board"], 6, selection["tasks"] if active_panel == "tasks" else None):
        put("  " + line)
    put("-" * min(width - 1, 78))

    put("EVENT STREAM (recent):")
    for line in render_event_lines(snapshot["event_stream"], 6, selection["events"] if active_panel == "events" else None):
        put("  " + line)

    stdscr.refresh()


def draw_drilldown(stdscr, detail: dict) -> None:
    stdscr.erase()
    height, width = stdscr.getmaxyx()
    stdscr.addnstr(0, 0, "MAP Mission Control detail (read-only) -- esc returns, r refreshes, q quits", max(0, width - 1))
    for row, line in enumerate(render_drilldown_lines(detail, max(1, height - 3)), start=2):
        if row < height - 1:
            stdscr.addnstr(row, 0, line, max(0, width - 1))
    stdscr.refresh()


def draw_help(stdscr) -> None:
    stdscr.erase()
    stdscr.addnstr(0, 0, "Read-only keybindings:", 78)
    row = 1
    for key, action in READ_ONLY_KEYBINDINGS.items():
        stdscr.addnstr(row, 0, f"  {key:<8} {action}", 78)
        row += 1
    row += 1
    stdscr.addnstr(row, 0, "Intervention keys (present, disabled this prototype):", 78)
    row += 1
    for key, action in DISABLED_INTERVENTION_KEYBINDINGS.items():
        stdscr.addnstr(row, 0, f"  {key:<8} {action}", 78)
        row += 1
    stdscr.addnstr(row + 1, 0, "Press any key to return.", 78)
    stdscr.refresh()
    stdscr.getch()


def _main_loop(stdscr) -> int:
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.timeout(1000)

    snapshot = build_dashboard_snapshot()
    active_panel = "attention"
    selection = {"attention": 0, "tasks": 0, "agents": 0, "events": 0}
    detail = None
    last_refresh = time.monotonic()
    draw(stdscr, snapshot, active_panel, selection)

    while True:
        try:
            ch = stdscr.getch()
        except curses.error:
            ch = -1

        if ch == ord("q"):
            return 0
        if ch == ord("r"):
            snapshot = build_dashboard_snapshot()
            selection = _bounded_selection(selection, snapshot)
            detail = selected_drilldown(snapshot, active_panel, selection) if detail else None
            last_refresh = time.monotonic()
            draw_drilldown(stdscr, detail) if detail else draw(stdscr, snapshot, active_panel, selection)
            continue
        if ch == ord("?"):
            draw_help(stdscr)
            draw_drilldown(stdscr, detail) if detail else draw(stdscr, snapshot, active_panel, selection)
            continue
        if ch in (ord("\t"),):
            active_panel = PANELS[(PANELS.index(active_panel) + 1) % len(PANELS)]
            detail = None
            draw(stdscr, snapshot, active_panel, selection)
            continue
        if ch in (ord("t"), ord("a"), ord("!"), ord("e")):
            active_panel = {ord("t"): "tasks", ord("a"): "agents", ord("!"): "attention", ord("e"): "events"}[ch]
            detail = None
            draw(stdscr, snapshot, active_panel, selection)
            continue
        if ch in (curses.KEY_DOWN, ord("j")):
            count = _panel_counts(snapshot)[active_panel]
            if count:
                selection[active_panel] = (selection[active_panel] + 1) % count
            detail = None
            draw(stdscr, snapshot, active_panel, selection)
            continue
        if ch in (curses.KEY_UP, ord("k")):
            count = _panel_counts(snapshot)[active_panel]
            if count:
                selection[active_panel] = (selection[active_panel] - 1) % count
            detail = None
            draw(stdscr, snapshot, active_panel, selection)
            continue
        if ch in (10, 13, curses.KEY_ENTER):
            detail = selected_drilldown(snapshot, active_panel, selection)
            if detail:
                draw_drilldown(stdscr, detail)
            continue
        if ch == 27:  # esc
            detail = None
            draw(stdscr, snapshot, active_panel, selection)
            continue
        # Every intervention key remains accepted but no-op in this prototype.

        if time.monotonic() - last_refresh > REFRESH_SECONDS:
            snapshot = build_dashboard_snapshot()
            selection = _bounded_selection(selection, snapshot)
            detail = selected_drilldown(snapshot, active_panel, selection) if detail else None
            last_refresh = time.monotonic()
            draw_drilldown(stdscr, detail) if detail else draw(stdscr, snapshot, active_panel, selection)


def run_app() -> int:
    return curses.wrapper(_main_loop)


if __name__ == "__main__":
    raise SystemExit(run_app())
