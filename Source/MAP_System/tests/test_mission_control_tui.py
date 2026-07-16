#!/usr/bin/env python3
"""Tests for the read-only mission-control TUI prototype (TASK-160)."""

from __future__ import annotations

import inspect
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

import MAP_System.scripts.mission_control_tui as mct  # noqa: E402
from MAP_System.scripts.mission_control_tui import (  # noqa: E402
    get_vitals,
    get_flight_board,
    get_attention_queue,
    get_event_stream,
    get_dead_letter_summary,
    get_live_liveness_snapshot,
    get_roster,
    get_task_record,
    get_task_drilldown,
    get_agent_drilldown,
    get_attention_drilldown,
    build_dashboard_snapshot,
    check_source_drift,
    READ_ONLY_KEYBINDINGS,
    DISABLED_INTERVENTION_KEYBINDINGS,
)
import MAP_System.scripts._mission_control_app as mca  # noqa: E402
from MAP_System.scripts._mission_control_app import (  # noqa: E402
    render_vitals_line,
    render_roster_lines,
    flight_board_items,
    render_flight_board_lines,
    render_attention_lines,
    render_event_lines,
    render_drilldown_lines,
    selected_drilldown,
)

FIXTURE_SNAPSHOT = {
    "next_route": "review",
    "ready_tasks": ["TASK-A"],
    "submitted_tasks": ["TASK-B"],
    "in_progress_tasks": [],
    "blocked_tasks": ["TASK-C"],
    "dispatch_blocked_tasks": [],
    "policy_gated_tasks": [],
    "policy_rejected_tasks": [],
    "policy_results": [],
    "halt_state": {"state": "repair_only", "reason": "validator_blocking_anomaly", "target": "TASK-B"},
    "available_agents": ["codex", "claude"],
}

FIXTURE_ROSTER = [
    {"agent_id": "codex-lab-x", "state": "working", "active_task": "TASK-A", "lane": "core", "evidence": "hcom:active"},
    {"agent_id": "claude-lab-y", "state": "broken", "active_task": "TASK-Z", "lane": "core", "evidence": "status:available;no_hcom_data"},
    {"agent_id": "claude-lab-w", "state": "suspect", "active_task": None, "lane": "core", "evidence": "no_hcom_data"},
]


def test_get_vitals_derives_counts_from_snapshot() -> None:
    vitals = get_vitals(FIXTURE_SNAPSHOT)
    assert vitals["next_route"] == "review"
    assert vitals["ready_count"] == 1
    assert vitals["submitted_count"] == 1
    assert vitals["blocked_count"] == 1
    assert vitals["halt_state"] == "repair_only"


def test_get_flight_board_maps_queues() -> None:
    board = get_flight_board(FIXTURE_SNAPSHOT)
    assert board["ready"] == ["TASK-A"]
    assert board["submitted"] == ["TASK-B"]
    assert board["blocked"] == ["TASK-C"]
    assert board["policy_gated"] == []
    assert board["policy_rejected"] == []


def test_flight_board_maps_policy_queues() -> None:
    snapshot = {
        **FIXTURE_SNAPSHOT,
        "policy_gated_tasks": ["TASK-G"],
        "policy_rejected_tasks": ["TASK-R"],
    }
    board = get_flight_board(snapshot)
    assert board["policy_gated"] == ["TASK-G"]
    assert board["policy_rejected"] == ["TASK-R"]


def test_attention_queue_is_human_decisions_only() -> None:
    items = get_attention_queue(FIXTURE_SNAPSHOT, FIXTURE_ROSTER)
    kinds = {item["kind"] for item in items}
    assert "review_needed" in kinds
    assert "halt_active" in kinds
    assert "agent_attention" in kinds

    # Routine "working"/"idle" agents are not attention items.
    targets = {item.get("target") for item in items if item["kind"] == "agent_attention"}
    assert "codex-lab-x" not in targets
    assert "claude-lab-y" in targets  # broken
    assert "claude-lab-w" in targets  # suspect


def test_attention_queue_includes_policy_results_with_reasons() -> None:
    snapshot = {
        **FIXTURE_SNAPSHOT,
        "policy_gated_tasks": ["TASK-G"],
        "policy_rejected_tasks": ["TASK-R"],
        "policy_results": [
            {
                "task_id": "TASK-G",
                "decision": "require_approval",
                "candidate_worker": "core-dispatch",
                "approval_authority": "bigboss",
                "reasons": ["REQUIRE_CORE_DESTRUCTIVE_APPROVAL"],
            },
            {
                "task_id": "TASK-R",
                "decision": "reject",
                "candidate_worker": "visible-helper",
                "reasons": ["HELPER_FORBIDDEN_CAPABILITY"],
            },
        ],
    }
    items = get_attention_queue(snapshot, [])
    policy_items = {item["kind"]: item for item in items if item["kind"].startswith("policy_")}
    assert policy_items["policy_gate"]["target"] == "TASK-G"
    assert "REQUIRE_CORE_DESTRUCTIVE_APPROVAL" in policy_items["policy_gate"]["detail"]
    assert "bigboss" in policy_items["policy_gate"]["detail"]
    assert policy_items["policy_rejected"]["target"] == "TASK-R"
    assert "HELPER_FORBIDDEN_CAPABILITY" in policy_items["policy_rejected"]["detail"]


def test_attention_queue_includes_drift_and_dead_letter_pressure() -> None:
    items = get_attention_queue(
        {**FIXTURE_SNAPSHOT, "submitted_tasks": [], "halt_state": {"state": "clear"}},
        [],
        drift={"drifted": True, "detail": "task-file TASK-X status mismatch"},
        dead_letter={"queued": 2, "queue_log": "MAP_System/dead_letters/dead_letters.jsonl", "error": None},
    )
    kinds = {item["kind"] for item in items}
    assert "source_drift" in kinds
    assert "dead_letter_queue" in kinds


def test_attention_queue_empty_when_clear_and_healthy() -> None:
    clean_snapshot = {**FIXTURE_SNAPSHOT, "submitted_tasks": [], "halt_state": {"state": "clear"}}
    healthy_roster = [{"agent_id": "a", "state": "working", "active_task": "T", "lane": "core", "evidence": "x"}]
    items = get_attention_queue(clean_snapshot, healthy_roster)
    assert items == []


def test_get_dead_letter_summary_counts_queued_latest_records() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        queue_log = Path(tmp) / "dead_letters.jsonl"
        queue_log.write_text(
            "\n".join([
                json.dumps({"dead_letter_id": "DLQ-1", "replay_status": "queued", "reason": "handler_crash"}),
                json.dumps({"dead_letter_id": "DLQ-2", "replay_status": "queued", "reason": "handler_crash"}),
                json.dumps({"dead_letter_id": "DLQ-1", "replay_status": "replayed", "reason": "handler_crash"}),
            ]) + "\n",
            encoding="utf-8",
        )
        summary = get_dead_letter_summary(queue_log)
    assert summary["queued"] == 1
    assert summary["error"] is None


def test_get_dead_letter_summary_surfaces_unreadable_queue() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        queue_log = Path(tmp) / "dead_letters.jsonl"
        queue_log.write_text("{not-json}\n", encoding="utf-8")
        summary = get_dead_letter_summary(queue_log)
    assert summary["queued"] is None
    assert summary["error"]


def test_get_live_liveness_snapshot_accepts_raw_hcom_list() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        status_path = base / "status.json"
        status_path.write_text(json.dumps({
            "agents": {
                "codex-lab-mozu": {"status": "available", "reason": None},
                "codex-lab-limo": {"status": "standby", "reason": "awaiting_work"},
            }
        }), encoding="utf-8")

        db_path = base / "map.db"
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE tasks (task_id TEXT, status TEXT, claimed_by TEXT, lease_expires_at TEXT)")
        conn.commit()
        conn.close()

        roster = get_live_liveness_snapshot(
            raw_hcom=[{"name": "codex-lab-mozu", "status": "active", "status_age_seconds": 0}],
            status_path=status_path,
            db_path=db_path,
        )

    by_id = {record["agent_id"]: record for record in roster}
    assert by_id["codex-lab-mozu"]["state"] == "alive"
    assert by_id["codex-lab-mozu"]["evidence"] == "hcom:active"
    assert by_id["codex-lab-limo"]["state"] == "standby"


def test_get_roster_prefers_live_and_falls_back_to_markdown() -> None:
    real_live = mct.get_live_liveness_snapshot
    real_markdown = mct.get_liveness_snapshot
    try:
        mct.get_live_liveness_snapshot = lambda: [
            {"agent_id": "live-agent", "state": "alive", "active_task": None, "lane": "core", "evidence": "hcom:active"}
        ]
        assert get_roster()[0]["agent_id"] == "live-agent"

        mct.get_live_liveness_snapshot = lambda: []
        mct.get_liveness_snapshot = lambda liveness_md=None: [
            {"agent_id": "fallback-agent", "state": "suspect", "active_task": None, "lane": "core", "evidence": "markdown"}
        ]
        assert get_roster()[0]["agent_id"] == "fallback-agent"
    finally:
        mct.get_live_liveness_snapshot = real_live
        mct.get_liveness_snapshot = real_markdown


def test_live_liveness_snapshot_composes_reaper_helpers() -> None:
    real_normalize = mct.normalize_hcom_status
    real_build = mct.build_liveness_records
    calls = []

    class Record:
        agent_id = "agent-x"
        state = "alive"
        active_task = None
        lane = "core"
        evidence = "fake"

    try:
        def fake_normalize(raw):
            calls.append(("normalize", raw))
            return {"agent-x": {"status": "active"}}

        def fake_build_liveness_records(**kwargs):
            calls.append(("build", kwargs["hcom_status_by_agent"]))
            return [Record()]

        mct.normalize_hcom_status = fake_normalize
        mct.build_liveness_records = fake_build_liveness_records

        roster = get_live_liveness_snapshot(raw_hcom=[{"name": "agent-x", "status": "active"}])
    finally:
        mct.normalize_hcom_status = real_normalize
        mct.build_liveness_records = real_build

    assert roster == [{"agent_id": "agent-x", "state": "alive", "active_task": None, "lane": "core", "evidence": "fake"}]
    assert calls == [
        ("normalize", [{"name": "agent-x", "status": "active"}]),
        ("build", {"agent-x": {"status": "active"}}),
    ]


def test_get_task_record_reads_task_json() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        task_dir = Path(tmp)
        (task_dir / "TASK-X.json").write_text(json.dumps({"task_id": "TASK-X", "title": "Example"}), encoding="utf-8")
        record = get_task_record("TASK-X", task_dir)
    assert record == {"task_id": "TASK-X", "title": "Example"}


def test_get_task_drilldown_uses_runner_events_policy_and_task_file() -> None:
    snapshot = {
        **FIXTURE_SNAPSHOT,
        "policy_gated_tasks": ["TASK-A"],
        "policy_results": [
            {
                "task_id": "TASK-A",
                "decision": "require_approval",
                "candidate_worker": "core-dispatch",
                "reasons": ["REQUIRE_CORE_DESTRUCTIVE_APPROVAL"],
            }
        ],
        "halt_state": {"state": "repair_only", "reason": "validator", "target": "TASK-A"},
    }
    events = [
        {"created_at": "t1", "type": "PROGRESS", "task_id": "TASK-Z", "summary": "other"},
        {"created_at": "t2", "type": "SUBMISSION", "task_id": "TASK-A", "summary": "submitted"},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        task_dir = Path(tmp)
        (task_dir / "TASK-A.json").write_text(json.dumps({"task_id": "TASK-A", "title": "Task A", "status": "READY"}), encoding="utf-8")
        detail = get_task_drilldown("TASK-A", snapshot, events, task_dir)

    assert detail["kind"] == "task"
    assert detail["task"]["title"] == "Task A"
    assert "ready" in detail["queues"]
    assert "policy_gated" in detail["queues"]
    assert detail["policy_results"][0]["decision"] == "require_approval"
    assert detail["halt"]["target"] == "TASK-A"
    assert detail["recent_events"][0]["summary"] == "submitted"


def test_get_agent_drilldown_uses_roster_and_sender_events() -> None:
    events = [
        {"created_at": "t1", "type": "PROGRESS", "task_id": "TASK-A", "sender": "codex-lab-x", "summary": "worked"},
        {"created_at": "t2", "type": "PROGRESS", "task_id": "TASK-B", "sender": "other", "summary": "ignored"},
    ]
    detail = get_agent_drilldown("codex-lab-x", FIXTURE_ROSTER, events)
    assert detail["kind"] == "agent"
    assert detail["record"]["state"] == "working"
    assert detail["active_task"] == "TASK-A"
    assert detail["recent_events"][0]["sender"] == "codex-lab-x"


def test_get_attention_drilldown_routes_to_task_agent_or_status_detail() -> None:
    task_detail = get_attention_drilldown(
        {"kind": "review_needed", "target": "TASK-A", "detail": "review"},
        FIXTURE_SNAPSHOT,
        FIXTURE_ROSTER,
        [],
        drift={"drifted": False, "detail": "ok"},
        dead_letter={"queued": 0, "queue_log": "x", "error": None},
    )
    agent_detail = get_attention_drilldown(
        {"kind": "agent_attention", "target": "claude-lab-y", "detail": "broken"},
        FIXTURE_SNAPSHOT,
        FIXTURE_ROSTER,
        [],
        drift={"drifted": False, "detail": "ok"},
        dead_letter={"queued": 0, "queue_log": "x", "error": None},
    )
    drift_detail = get_attention_drilldown(
        {"kind": "source_drift", "target": "task_mirrors", "detail": "mismatch"},
        FIXTURE_SNAPSHOT,
        FIXTURE_ROSTER,
        [],
        drift={"drifted": True, "detail": "mismatch"},
        dead_letter={"queued": 0, "queue_log": "x", "error": None},
    )
    dead_letter_detail = get_attention_drilldown(
        {"kind": "dead_letter_queue", "target": "2 queued", "detail": "queue"},
        FIXTURE_SNAPSHOT,
        FIXTURE_ROSTER,
        [],
        drift={"drifted": False, "detail": "ok"},
        dead_letter={"queued": 2, "queue_log": "x", "error": None},
    )
    assert task_detail["task"]["target"] == "TASK-A"
    assert agent_detail["agent"]["record"]["agent_id"] == "claude-lab-y"
    assert drift_detail["drift"]["drifted"] is True
    assert dead_letter_detail["dead_letter"]["queued"] == 2


def test_get_event_stream_reads_real_log_tail() -> None:
    events = get_event_stream(limit=5)
    assert isinstance(events, list)
    assert len(events) <= 5
    for e in events:
        assert "type" in e
        assert "task_id" in e


def test_check_source_drift_against_real_clean_repo() -> None:
    drift = check_source_drift()
    assert drift["drifted"] is False, drift["detail"]


def test_build_dashboard_snapshot_has_all_required_panels() -> None:
    snapshot = build_dashboard_snapshot()
    for key in ("runner", "vitals", "roster", "flight_board", "attention_queue", "event_stream", "drift", "dead_letter"):
        assert key in snapshot


def test_read_only_keybindings_present_and_intervention_keys_disabled() -> None:
    for key in ("q", "r", "tab", "up/down", "j/k", "enter", "esc", "t", "a", "e", "!", "?"):
        assert key in READ_ONLY_KEYBINDINGS

    for key, action in DISABLED_INTERVENTION_KEYBINDINGS.items():
        assert "disabled" in action.lower()


def test_module_never_writes_to_map_state() -> None:
    """Structural guard for acceptance criterion 2: no write path exists.
    Checks the module source for anything that would mutate canonical
    MAP state -- SQLite write statements, file-open in write mode against
    tracked state, or subprocess calls to scripts that mutate state.
    """
    source = inspect.getsource(mct)
    forbidden_sql = ("INSERT INTO", "UPDATE ", "DELETE FROM", "CREATE TABLE", "ALTER TABLE", "DROP TABLE")
    for token in forbidden_sql:
        assert token not in source, f"found forbidden SQL token: {token}"

    assert 'open(' not in source or all(
        mode not in source for mode in ('"a"', "'a'", '"w"', "'w'")
    ), "module must not open files in append/write mode"

    forbidden_scripts = ("map_task.py", "export_to_files.py", "liveness_reaper.py --act", "release_task.py")
    for script in forbidden_scripts:
        assert script not in source, f"module must not shell out to a write-capable script: {script}"


def test_render_vitals_line_formats_key_fields() -> None:
    line = render_vitals_line(get_vitals(FIXTURE_SNAPSHOT))
    assert "route=review" in line
    assert "ready=1" in line
    assert "halt=repair_only" in line


def test_render_roster_lines_shows_state_and_task() -> None:
    lines = render_roster_lines(FIXTURE_ROSTER, max_rows=10, selected=1)
    assert any("codex-lab-x" in l and "working" in l and "TASK-A" in l for l in lines)
    assert any(l.startswith(">[") and "claude-lab-y" in l and "broken" in l for l in lines)


def test_render_flight_board_lines_labels_each_queue() -> None:
    snapshot = {
        **FIXTURE_SNAPSHOT,
        "dispatch_blocked_tasks": ["TASK-D"],
        "policy_gated_tasks": ["TASK-G"],
        "policy_rejected_tasks": ["TASK-R"],
    }
    items = flight_board_items(get_flight_board(snapshot))
    assert {"label": "POLICY-GATE", "task_id": "TASK-G"} in items
    lines = render_flight_board_lines(get_flight_board(snapshot), max_rows=10)
    assert any("READY" in l and "TASK-A" in l for l in lines)
    assert any("SUBMITTED" in l and "TASK-B" in l for l in lines)
    assert any("BLOCKED" in l and "TASK-C" in l for l in lines)
    assert any("DISPATCH-BLK" in l and "TASK-D" in l for l in lines)
    assert any("POLICY-GATE" in l and "TASK-G" in l for l in lines)
    assert any("POLICY-REJ" in l and "TASK-R" in l for l in lines)


def test_render_attention_lines_include_all_kinds() -> None:
    items = get_attention_queue(FIXTURE_SNAPSHOT, FIXTURE_ROSTER)
    lines = render_attention_lines(items, max_rows=10, selected=0)
    assert len(lines) == len(items)
    assert lines[0].startswith(">!")
    assert all(l[1:].startswith("!") for l in lines)


def test_render_event_lines_truncates_to_max_rows() -> None:
    fake_events = [
        {
            "created_at": f"t{i}",
            "type": "PROGRESS",
            "task_id": f"TASK-{i}",
            "summary": "x",
            "trace_id": f"task:TASK-{i}",
        }
        for i in range(10)
    ]
    lines = render_event_lines(fake_events, max_rows=3, selected=2)
    assert len(lines) == 3
    # Most recent events (highest i) should be the ones shown.
    assert "TASK-9" in lines[-1]
    assert "trace=task:TASK-9" in lines[-1]
    assert lines[-1].startswith(">")


def test_render_event_lines_handles_missing_trace_id() -> None:
    lines = render_event_lines(
        [{"created_at": "t", "type": "PROGRESS", "task_id": "TASK-1", "summary": "legacy"}],
        max_rows=3,
    )
    assert "trace=-" in lines[0]


def test_render_drilldown_lines_formats_task_agent_attention_and_event() -> None:
    task_lines = render_drilldown_lines(
        {
            "kind": "task",
            "target": "TASK-A",
            "task": {"title": "Task A", "status": "READY", "owner": "owner", "claimed_by": None},
            "queues": ["ready"],
            "policy_results": [],
            "recent_events": [{"created_at": "t", "type": "PROGRESS", "trace_id": "task:TASK-A", "summary": "s"}],
        },
        max_rows=10,
    )
    agent_lines = render_drilldown_lines(
        {
            "kind": "agent",
            "target": "codex-lab-x",
            "record": FIXTURE_ROSTER[0],
            "active_task": "TASK-A",
            "recent_events": [{"created_at": "t", "type": "PROGRESS", "task_id": "TASK-A", "trace_id": "task:TASK-A"}],
        },
        max_rows=10,
    )
    attention_lines = render_drilldown_lines(
        {"kind": "attention", "target": "TASK-A", "item": {"kind": "review_needed", "detail": "review"}},
        max_rows=10,
    )
    event_lines = render_drilldown_lines(
        {
            "kind": "event",
            "target": "TASK-A",
            "event": {
                "created_at": "t",
                "type": "PROGRESS",
                "task_id": "TASK-A",
                "trace_id": "task:TASK-A",
                "sender": "a",
                "summary": "s",
            },
        },
        max_rows=10,
    )
    assert "TASK: TASK-A" in task_lines[0]
    assert any("title: Task A" in line for line in task_lines)
    assert any("trace=task:TASK-A" in line for line in task_lines)
    assert any("state: working" in line for line in agent_lines)
    assert any("trace=task:TASK-A" in line for line in agent_lines)
    assert any("attention_kind: review_needed" in line for line in attention_lines)
    assert any("trace_id: task:TASK-A" in line for line in event_lines)
    assert any("summary: s" in line for line in event_lines)


def test_selected_drilldown_uses_active_panel_and_selection() -> None:
    snapshot = {
        "runner": FIXTURE_SNAPSHOT,
        "vitals": get_vitals(FIXTURE_SNAPSHOT),
        "roster": FIXTURE_ROSTER,
        "flight_board": get_flight_board(FIXTURE_SNAPSHOT),
        "attention_queue": get_attention_queue(FIXTURE_SNAPSHOT, FIXTURE_ROSTER),
        "event_stream": [
            {"created_at": "t1", "type": "PROGRESS", "task_id": "TASK-A", "sender": "codex-lab-x", "summary": "x"},
        ],
        "drift": {"drifted": False, "detail": "ok"},
        "dead_letter": {"queued": 0, "queue_log": "x", "error": None},
    }
    assert selected_drilldown(snapshot, "tasks", {"tasks": 0})["target"] == "TASK-A"
    assert selected_drilldown(snapshot, "agents", {"agents": 1})["target"] == "claude-lab-y"
    assert selected_drilldown(snapshot, "attention", {"attention": 0})["kind"] == "attention"
    assert selected_drilldown(snapshot, "events", {"events": 0})["kind"] == "event"


def test_rendering_module_never_writes_to_map_state() -> None:
    """Same structural guard as the data layer, applied to the rendering
    module -- the interactive App must only ever render
    build_dashboard_snapshot()'s output, never mutate state itself.
    """
    source = inspect.getsource(mca)
    forbidden_sql = ("INSERT INTO", "UPDATE ", "DELETE FROM", "CREATE TABLE", "ALTER TABLE", "DROP TABLE")
    for token in forbidden_sql:
        assert token not in source, f"found forbidden SQL token: {token}"

    forbidden_scripts = ("map_task.py", "export_to_files.py", "liveness_reaper.py --act", "release_task.py")
    for script in forbidden_scripts:
        assert script not in source, f"rendering module must not shell out to a write-capable script: {script}"


def main() -> int:
    tests = [
        test_get_vitals_derives_counts_from_snapshot,
        test_get_flight_board_maps_queues,
        test_flight_board_maps_policy_queues,
        test_attention_queue_is_human_decisions_only,
        test_attention_queue_includes_policy_results_with_reasons,
        test_attention_queue_includes_drift_and_dead_letter_pressure,
        test_attention_queue_empty_when_clear_and_healthy,
        test_get_dead_letter_summary_counts_queued_latest_records,
        test_get_dead_letter_summary_surfaces_unreadable_queue,
        test_get_live_liveness_snapshot_accepts_raw_hcom_list,
        test_get_roster_prefers_live_and_falls_back_to_markdown,
        test_live_liveness_snapshot_composes_reaper_helpers,
        test_get_task_record_reads_task_json,
        test_get_task_drilldown_uses_runner_events_policy_and_task_file,
        test_get_agent_drilldown_uses_roster_and_sender_events,
        test_get_attention_drilldown_routes_to_task_agent_or_status_detail,
        test_get_event_stream_reads_real_log_tail,
        test_check_source_drift_against_real_clean_repo,
        test_build_dashboard_snapshot_has_all_required_panels,
        test_read_only_keybindings_present_and_intervention_keys_disabled,
        test_module_never_writes_to_map_state,
        test_render_vitals_line_formats_key_fields,
        test_render_roster_lines_shows_state_and_task,
        test_render_flight_board_lines_labels_each_queue,
        test_render_attention_lines_include_all_kinds,
        test_render_event_lines_truncates_to_max_rows,
        test_render_event_lines_handles_missing_trace_id,
        test_render_drilldown_lines_formats_task_agent_attention_and_event,
        test_selected_drilldown_uses_active_panel_and_selection,
        test_rendering_module_never_writes_to_map_state,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
