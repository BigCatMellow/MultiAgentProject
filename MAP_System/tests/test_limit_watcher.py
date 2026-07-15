#!/usr/bin/env python3
"""Tests for limit_watcher decision logic (TASK-080). Pure functions only."""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from limit_watcher import decide_nudges, detect_silent_stops, parse_resume_after

NOW = datetime(2026, 7, 2, 12, 0, 0, tzinfo=timezone.utc)


def status(**agents):
    return {"agents": agents}


def entry(status_val="standby", reason="out_of_tokens", resume_after=None):
    return {"status": status_val, "reason": reason, "resume_after": resume_after}


def test_parse_resume_after():
    assert parse_resume_after("2026-07-02T11:00:00+00:00") is not None
    assert parse_resume_after("2026-07-02T11:00:00Z") is not None
    naive = parse_resume_after("2026-07-02T11:00:00")
    assert naive is not None and naive.tzinfo is not None  # naive -> local tz
    assert parse_resume_after("when operator restores token budget") is None
    assert parse_resume_after(None) is None
    assert parse_resume_after("") is None


def test_due_agent_is_nudged():
    past = (NOW - timedelta(minutes=5)).isoformat()
    nudges, unparseable = decide_nudges(
        status(codex=entry(resume_after=past)), {"nudged": {}}, NOW)
    assert nudges == [("codex", past)]
    assert unparseable == []


def test_not_yet_due_is_skipped():
    future = (NOW + timedelta(hours=2)).isoformat()
    nudges, _ = decide_nudges(
        status(codex=entry(resume_after=future)), {"nudged": {}}, NOW)
    assert nudges == []


def test_one_nudge_per_window():
    past = (NOW - timedelta(minutes=5)).isoformat()
    state = {"nudged": {"codex": past}}
    nudges, _ = decide_nudges(status(codex=entry(resume_after=past)), state, NOW)
    assert nudges == []  # spawn-loop guard
    # but a NEW resume_after value (next limit event) is nudgeable again
    newer = (NOW - timedelta(minutes=1)).isoformat()
    nudges, _ = decide_nudges(status(codex=entry(resume_after=newer)), state, NOW)
    assert nudges == [("codex", newer)]


def test_unparseable_reported_once():
    raw = "when operator restores token budget"
    st = status(antigravity=entry(resume_after=raw))
    nudges, unparseable = decide_nudges(st, {"nudged": {}, "warned_unparseable": {}}, NOW)
    assert nudges == []
    assert unparseable == [("antigravity", raw)]
    nudges, unparseable = decide_nudges(
        st, {"nudged": {}, "warned_unparseable": {"antigravity": raw}}, NOW)
    assert unparseable == []  # already warned for this exact value


def test_available_or_other_reason_never_nudged():
    past = (NOW - timedelta(minutes=5)).isoformat()
    nudges, _ = decide_nudges(
        status(a=entry(status_val="available", resume_after=past),
               b=entry(reason="long_term_unavailable", resume_after=past)),
        {"nudged": {}}, NOW)
    assert nudges == []


def test_silent_stop_detection():
    st = status(rose={"status": "available"}, limo={"status": "standby", "reason": "out_of_tokens"})
    # rose vanished without status update -> silent; limo recorded standby -> not silent
    stops = detect_silent_stops(["rose", "limo"], [], st, set())
    assert stops == ["rose"]
    # already reported -> not repeated
    assert detect_silent_stops(["rose"], [], st, {"rose"}) == []
    # still live -> nothing
    assert detect_silent_stops(["rose"], ["rose"], st, set()) == []


def test_empty_hcom_list_is_data_not_failure():
    """Regression (TASK-080 review finding 1, carried into v2's hcom_snapshot):
    a successful empty hcom list must return {}, not None, so presumed-down
    detection still runs when ALL previously live agents have vanished."""
    import limit_watcher as lw

    class FakeResult:
        def __init__(self, code, stdout):
            self.returncode = code
            self.stdout = stdout

    real_run = lw.subprocess.run
    try:
        lw.subprocess.run = lambda *a, **k: FakeResult(0, "[]")
        assert lw.hcom_snapshot() == {}  # empty success -> data
        lw.subprocess.run = lambda *a, **k: FakeResult(
            0, '[{"name":"rose","status":"active","status_age_seconds":1}]')
        assert list(lw.hcom_snapshot()) == ["rose"]
        lw.subprocess.run = lambda *a, **k: FakeResult(1, "")
        assert lw.hcom_snapshot() is None  # failure -> None
        lw.subprocess.run = lambda *a, **k: FakeResult(0, "not json")
        assert lw.hcom_snapshot() is None  # garbage -> None
    finally:
        lw.subprocess.run = real_run
    # all-vanished end-to-end: everyone previously live becomes an incident
    from limit_watcher import detect_presumed_down
    st = status(rose={"status": "available"}, limo={"status": "available"})
    assert detect_presumed_down(["rose", "limo"], {}, st, incidents={}) == ["limo", "rose"]


def test_overnight_incident_shape():
    """Regression (TASK-083, hcom #15260): a session dies with no final turn.
    It stays LISTED in hcom with its last status, but status_age grows
    unbounded, and status.json still says available. v1 missed this entirely;
    v2 must classify it not-live and open an incident."""
    from limit_watcher import classify_live, detect_presumed_down

    dead = {"status": "active", "status_age_seconds": 21600}   # 6h stale
    fresh = {"status": "listening", "status_age_seconds": 5}
    assert classify_live(dead) is False
    assert classify_live(fresh) is True
    assert classify_live({"status": "stopped", "status_age_seconds": 2}) is False

    snapshot = {"rose": dead, "limo": fresh}
    st = status(rose={"status": "available"}, limo={"status": "available"})
    down = detect_presumed_down(["rose", "limo"], snapshot, st, incidents={})
    assert down == ["rose"]
    # deliberately recorded agents are NOT incidents (v1 path owns them)
    st2 = status(rose={"status": "standby", "reason": "out_of_tokens",
                       "resume_after": "2026-07-02T15:00:00"}, limo={"status": "available"})
    assert detect_presumed_down(["rose", "limo"], snapshot, st2, incidents={}) == []
    # open incident not re-detected
    assert detect_presumed_down(["rose"], {"rose": dead}, st, incidents={"rose": {}}) == []


def test_prune_absent_session_tracking_removes_historical_helpers():
    """TASK-176: RnS must not keep probe-resuming stale helper sessions that
    survived only in limit-watcher-state.json across lab restarts."""
    from limit_watcher import prune_absent_session_tracking

    state = {
        "last_live": ["codex-lab-mozu", "map613-old-helper"],
        "incidents": {
            "claude-lab-fimo": {"probes_sent": 0},
            "durable-agent": {"probes_sent": 1},
        },
    }
    st = {"agents": {"durable-agent": {"status": "available"}}}
    snapshot = {"codex-lab-mozu": {"status": "active", "status_age_seconds": 1}}

    pruned = prune_absent_session_tracking(state, st, snapshot)

    assert pruned == {
        "pruned_incidents": ["claude-lab-fimo"],
        "pruned_last_live": ["map613-old-helper"],
    }
    assert state["last_live"] == ["codex-lab-mozu"]
    assert list(state["incidents"]) == ["durable-agent"]


def test_prune_preserves_registered_agent_for_presumed_down_detection():
    """A durable registered agent missing from hcom is still a real
    presumed-down candidate; pruning must only remove names absent from both
    sources."""
    from limit_watcher import detect_presumed_down, prune_absent_session_tracking

    state = {"last_live": ["rose"], "incidents": {}}
    st = status(rose={"status": "available"})
    snapshot = {}

    pruned = prune_absent_session_tracking(state, st, snapshot)

    assert pruned == {"pruned_incidents": [], "pruned_last_live": []}
    assert detect_presumed_down(state["last_live"], snapshot, st, incidents={}) == ["rose"]


def test_probe_backoff_schedule():
    from limit_watcher import probe_action, PROBE_SCHEDULE_MINUTES

    detected = NOW.isoformat()
    inc = {"detected_at": detected, "reset_at": None, "probes_sent": 0,
           "reset_nudged": False, "gave_up": False}
    assert probe_action(inc, NOW + timedelta(minutes=5)) == "wait"
    assert probe_action(inc, NOW + timedelta(minutes=16)) == "nudge"
    inc["probes_sent"] = 1
    assert probe_action(inc, NOW + timedelta(minutes=20)) == "wait"
    assert probe_action(inc, NOW + timedelta(minutes=46)) == "nudge"
    inc["probes_sent"] = len(PROBE_SCHEDULE_MINUTES)
    assert probe_action(inc, NOW + timedelta(hours=9)) == "give_up"
    inc["gave_up"] = True
    assert probe_action(inc, NOW + timedelta(hours=10)) == "wait"  # gives up once


def test_probe_action_with_known_reset():
    """Regression (TASK-083 review finding 1): retries after the scheduled
    reset nudge must anchor to the nudge time, not detected_at — otherwise
    every earlier backoff slot is instantly overdue and consecutive polls
    fire probes back-to-back."""
    from limit_watcher import probe_action

    inc = {"detected_at": NOW.isoformat(),
           "reset_at": (NOW + timedelta(hours=2)).isoformat(),
           "probes_sent": 0, "reset_nudged": False, "gave_up": False}
    assert probe_action(inc, NOW + timedelta(minutes=30)) == "wait"   # before reset: no probes
    assert probe_action(inc, NOW + timedelta(hours=2, minutes=1)) == "nudge"
    # reset nudge fires; retries re-anchor to its timestamp
    nudge_time = NOW + timedelta(hours=2, minutes=1)
    inc["reset_nudged"] = True
    inc["reset_nudged_at"] = nudge_time.isoformat()
    assert probe_action(inc, nudge_time + timedelta(minutes=2)) == "wait"   # NOT instantly overdue
    assert probe_action(inc, nudge_time + timedelta(minutes=16)) == "nudge" # first retry slot
    inc["probes_sent"] = 1
    assert probe_action(inc, nudge_time + timedelta(minutes=20)) == "wait"
    assert probe_action(inc, nudge_time + timedelta(minutes=46)) == "nudge"


def test_reset_time_parsing():
    from limit_watcher import parse_reset_time_from_text

    now = NOW.replace(hour=10)  # 10:00 UTC
    got = parse_reset_time_from_text("5-hour limit reached ... resets 3pm", now)
    assert got is not None and (got.hour, got.minute) == (15, 0) and got > now
    got = parse_reset_time_from_text("limit reached. resets at 9:30am", now)
    assert got is not None and (got.hour, got.minute) == (9, 30) and got > now  # tomorrow
    got = parse_reset_time_from_text("usage resets at 23:15 tonight", now)
    assert got is not None and (got.hour, got.minute) == (23, 15)
    assert parse_reset_time_from_text("no limit text here", now) is None
    # last mention wins
    got = parse_reset_time_from_text("resets 1pm ... actually resets 4pm", now)
    assert got.hour == 16


def test_process_bound_liveness_contract():
    """TASK-084: process_bound separates idle-but-alive (check-in territory)
    from dead-with-frozen-status (incident territory). Age heuristic remains
    the fallback when process_bound is absent (TASK-083 incident shape)."""
    from limit_watcher import classify_live

    assert classify_live({"status": "listening", "status_age_seconds": 3 * 3600,
                          "process_bound": True}) is True     # idle but alive
    assert classify_live({"status": "active", "status_age_seconds": 3 * 3600,
                          "process_bound": False}) is False   # zombie entry
    assert classify_live({"status": "active", "status_age_seconds": 21600}) is False  # fallback
    assert classify_live({"status": "listening", "status_age_seconds": 5,
                          "process_bound": True}) is True


def test_checkin_decision_logic():
    """TASK-084 / IDEA-0007: check-in nudges hit only live agents idle 2h+
    with no claim and no declaration. Every safety boundary from the idea
    card is a suppression case."""
    from limit_watcher import decide_checkins

    idle3h = {"status": "listening", "status_age_seconds": 3 * 3600, "process_bound": True}
    idle1h = {"status": "listening", "status_age_seconds": 3600, "process_bound": True}
    working = {"status": "active", "status_age_seconds": 3 * 3600, "process_bound": True}
    dead = {"status": "listening", "status_age_seconds": 7 * 3600, "process_bound": False}

    st = status(rose={"status": "available"}, limo={"status": "available"})

    # the drifted agent gets a check-in
    assert decide_checkins({"rose": idle3h}, st, set(), {"checkins": {}}, NOW) == ["rose"]
    # blocked/waiting sessions are stuck, not drifting -- never check-in nudged
    # (TASK-084 review finding 1)
    blocked3h = {"status": "blocked", "status_age_seconds": 3 * 3600, "process_bound": True}
    waiting3h = {"status": "waiting", "status_age_seconds": 3 * 3600, "process_bound": True}
    assert decide_checkins({"rose": blocked3h}, st, set(), {"checkins": {}}, NOW) == []
    assert decide_checkins({"rose": waiting3h}, st, set(), {"checkins": {}}, NOW) == []
    # short idle, visibly active, or dead: no check-in
    assert decide_checkins({"rose": idle1h}, st, set(), {"checkins": {}}, NOW) == []
    assert decide_checkins({"rose": working}, st, set(), {"checkins": {}}, NOW) == []
    assert decide_checkins({"rose": dead}, st, set(), {"checkins": {}}, NOW) == []
    # an IN_PROGRESS claim suppresses
    assert decide_checkins({"rose": idle3h}, st, {"rose"}, {"checkins": {}}, NOW) == []
    # a declared reason suppresses (awaiting_work, out_of_tokens, anything)
    st_declared = status(rose={"status": "standby", "reason": "awaiting_work"})
    assert decide_checkins({"rose": idle3h}, st_declared, set(), {"checkins": {}}, NOW) == []
    # non-available durable status suppresses
    st_inactive = status(rose={"status": "inactive", "reason": None})
    assert decide_checkins({"rose": idle3h}, st_inactive, set(), {"checkins": {}}, NOW) == []
    # renudge throttle: one per window
    recent = {"checkins": {"rose": (NOW - timedelta(minutes=30)).isoformat()}}
    assert decide_checkins({"rose": idle3h}, st, set(), recent, NOW) == []
    old = {"checkins": {"rose": (NOW - timedelta(hours=3)).isoformat()}}
    assert decide_checkins({"rose": idle3h}, st, set(), old, NOW) == ["rose"]


def test_work_dispatch_logic():
    """TASK-095 / operator #17759: while claimable MAP work exists, idle
    listening agents with no claim and no declaration get a bounded nudge.
    Same safety boundaries as check-ins, shorter throttle, no 2h wait."""
    from limit_watcher import decide_work_nudges, describe_work

    idle5m = {"status": "listening", "status_age_seconds": 300, "process_bound": True}
    fresh = {"status": "listening", "status_age_seconds": 30, "process_bound": True}
    working = {"status": "active", "status_age_seconds": 300, "process_bound": True}
    dead = {"status": "listening", "status_age_seconds": 7 * 3600, "process_bound": False}

    st = status(rose={"status": "available"}, limo={"status": "available"})
    work = {"ready": [("TASK-050", "Fix flags", "codex")],
            "review": [("TASK-095", "Dispatch", "rose")],
            "rework": [], "stale_claim": []}

    # idle agent with claimable work gets a nudge
    assert decide_work_nudges({"rose": idle5m}, st, set(), work, {"work_nudges": {}}, NOW) == ["rose"]
    # empty queue: silence
    assert decide_work_nudges({"rose": idle5m}, st, set(), {}, {"work_nudges": {}}, NOW) == []
    # just-went-idle grace, visibly active, or dead session: no nudge
    assert decide_work_nudges({"rose": fresh}, st, set(), work, {"work_nudges": {}}, NOW) == []
    assert decide_work_nudges({"rose": working}, st, set(), work, {"work_nudges": {}}, NOW) == []
    assert decide_work_nudges({"rose": dead}, st, set(), work, {"work_nudges": {}}, NOW) == []
    # an open claim suppresses
    assert decide_work_nudges({"rose": idle5m}, st, {"rose"}, work, {"work_nudges": {}}, NOW) == []
    # declared standby / non-available durable status suppress
    st_declared = status(rose={"status": "standby", "reason": "awaiting_work"})
    assert decide_work_nudges({"rose": idle5m}, st_declared, set(), work, {"work_nudges": {}}, NOW) == []
    st_inactive = status(rose={"status": "inactive", "reason": None})
    assert decide_work_nudges({"rose": idle5m}, st_inactive, set(), work, {"work_nudges": {}}, NOW) == []
    # throttle: one per 30min window
    recent = {"work_nudges": {"rose": (NOW - timedelta(minutes=10)).isoformat()}}
    assert decide_work_nudges({"rose": idle5m}, st, set(), work, recent, NOW) == []
    old = {"work_nudges": {"rose": (NOW - timedelta(minutes=40)).isoformat()}}
    assert decide_work_nudges({"rose": idle5m}, st, set(), work, old, NOW) == ["rose"]
    # an agent whose only actionable item is reviewing their own submission
    # is not nudged (no-self-review)
    own_review_only = {"ready": [], "rework": [], "stale_claim": [],
                       "review": [("TASK-095", "Dispatch", "rose")]}
    assert decide_work_nudges({"rose": idle5m}, st, set(), own_review_only,
                              {"work_nudges": {}}, NOW) == []
    assert decide_work_nudges({"limo": idle5m}, st, set(), own_review_only,
                              {"work_nudges": {}}, NOW) == ["limo"]
    # describe_work: reviews exclude own tasks, rework only own
    assert "TASK-095" not in describe_work(work, "rose")
    assert "TASK-095" in describe_work(work, "limo")


def test_stale_claim_owner_nudge_logic():
    """TASK-119: stale IN_PROGRESS claims can hide work from recovered agents.
    RnS should target the stale claim owner, even when there is no READY work
    to dispatch, and throttle per task."""
    from limit_watcher import decide_stale_claim_owner_nudges

    claims = [
        {
            "task_id": "TASK-117",
            "title": "Archive/Retention System",
            "owner": "claude-lab-valo",
            "claimed_by": "claude-lab-valo",
            "lease_expires_at": (NOW - timedelta(minutes=5)).isoformat(),
        }
    ]

    due = decide_stale_claim_owner_nudges(claims, {"stale_claim_owner_nudges": {}}, NOW)

    assert list(due) == ["claude-lab-valo"]
    assert due["claude-lab-valo"][0]["task_id"] == "TASK-117"

    recent = {"stale_claim_owner_nudges": {"TASK-117": (NOW - timedelta(minutes=10)).isoformat()}}
    assert decide_stale_claim_owner_nudges(claims, recent, NOW) == {}

    old = {"stale_claim_owner_nudges": {"TASK-117": (NOW - timedelta(minutes=40)).isoformat()}}
    assert list(decide_stale_claim_owner_nudges(claims, old, NOW)) == ["claude-lab-valo"]


def test_terminal_session_classification():
    """TASK-186 / IDEA-0009: only durable inactive + a terminal reason counts.
    Anything else stays in normal RnS territory."""
    from limit_watcher import TERMINAL_SESSION_REASONS, is_terminal_session

    assert TERMINAL_SESSION_REASONS == {"session_superseded", "disposable_session_ended"}
    assert is_terminal_session({"status": "inactive", "reason": "session_superseded"}) is True
    assert is_terminal_session({"status": "inactive", "reason": "disposable_session_ended"}) is True
    # inactive without a terminal reason is NOT terminal
    assert is_terminal_session({"status": "inactive", "reason": None}) is False
    assert is_terminal_session({"status": "inactive", "reason": "out_of_tokens"}) is False
    # terminal reason without inactive status is NOT terminal
    assert is_terminal_session({"status": "standby", "reason": "session_superseded"}) is False
    assert is_terminal_session({"status": "available", "reason": "disposable_session_ended"}) is False
    assert is_terminal_session({}) is False


def test_close_terminal_incidents_pops_and_labels():
    """TASK-186: open incidents for now-terminal agents are popped and labeled
    closed_reason='terminal_session' — an explicit closure, not a silent drop.
    Non-terminal incidents stay open."""
    from limit_watcher import close_terminal_incidents

    state = {"incidents": {
        "zera": {"probes_sent": 6, "gave_up": True},
        "mozu": {"probes_sent": 1, "gave_up": False},
        "rose": {"probes_sent": 2, "gave_up": False},
    }}
    st = status(zera={"status": "inactive", "reason": "session_superseded"},
                mozu={"status": "inactive", "reason": "disposable_session_ended"},
                rose={"status": "available"})

    closed = close_terminal_incidents(state, st)

    assert [name for name, _ in closed] == ["mozu", "zera"]
    assert all(inc["closed_reason"] == "terminal_session" for _, inc in closed)
    # popped records keep their history (probes_sent etc.)
    assert dict(closed)["zera"]["probes_sent"] == 6
    assert list(state["incidents"]) == ["rose"]
    # idempotent: nothing terminal left to close
    assert close_terminal_incidents(state, st) == []


def test_detect_terminal_suppressions_selects_only_terminal_absentees():
    """TASK-186: mirror of detect_presumed_down, but selecting the absentees
    RnS must deliberately leave dead. The two sets never overlap: presumed-down
    skips any recorded reason, terminal requires one."""
    from limit_watcher import detect_presumed_down, detect_terminal_suppressions

    snapshot = {"limo": {"status": "listening", "status_age_seconds": 5}}
    st = status(zera={"status": "inactive", "reason": "session_superseded"},
                mozu={"status": "inactive", "reason": "disposable_session_ended"},
                rose={"status": "available"},
                limo={"status": "available"})
    prev_live = ["zera", "mozu", "rose", "limo"]

    assert detect_terminal_suppressions(prev_live, snapshot, st) == ["mozu", "zera"]
    # still-live agents are never suppression-reported
    assert detect_terminal_suppressions(["limo"], snapshot, st) == []
    # the non-terminal absentee remains presumed-down territory, terminal ones do not
    assert detect_presumed_down(prev_live, snapshot, st, incidents={}) == ["rose"]


def test_terminal_entries_suppressed_in_checkins_work_nudges_and_v1_nudges():
    """TASK-186: decide_checkins/decide_work_nudges/decide_nudges already
    suppress non-available/reason-set agents; these assertions pin that
    terminal entries stay suppressed there."""
    from limit_watcher import decide_checkins, decide_nudges, decide_work_nudges

    idle3h = {"status": "listening", "status_age_seconds": 3 * 3600, "process_bound": True}
    idle5m = {"status": "listening", "status_age_seconds": 300, "process_bound": True}
    work = {"ready": [("TASK-050", "Fix flags", "codex")],
            "review": [], "rework": [], "stale_claim": []}

    for reason in ("session_superseded", "disposable_session_ended"):
        st = status(rose={"status": "inactive", "reason": reason})
        assert decide_checkins({"rose": idle3h}, st, set(), {"checkins": {}}, NOW) == []
        assert decide_work_nudges({"rose": idle5m}, st, set(), work,
                                  {"work_nudges": {}}, NOW) == []
        # v1 recorded-reset path: terminal entries are never resume-nudged,
        # even with a passed resume_after lingering on the record
        past = (NOW - timedelta(minutes=5)).isoformat()
        st2 = status(rose={"status": "inactive", "reason": reason, "resume_after": past})
        nudges, unparseable = decide_nudges(st2, {"nudged": {}, "warned_unparseable": {}}, NOW)
        assert nudges == [] and unparseable == []


def test_send_nudge_resume_success_keeps_visible_terminal():
    import limit_watcher as lw

    class FakeResult:
        returncode = 0
        stdout = ""
        stderr = ""

    calls = []
    real_run = lw.subprocess.run
    try:
        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            return FakeResult()

        lw.subprocess.run = fake_run
        assert lw.send_nudge("claude-lab-mira") is True
    finally:
        lw.subprocess.run = real_run

    assert calls[0][:4] == ["hcom", "send", "@claude-lab-mira", "--intent"]
    assert calls[1][:6] == ["hcom", "r", "claude-lab-mira", "--terminal", "wezterm-tab", "--go"]
    assert "--headless" not in calls[1]
    assert len(calls) == 2


def test_send_nudge_active_session_fallback_sends_prompt():
    import limit_watcher as lw

    class FakeResult:
        def __init__(self, code=0, stdout="", stderr=""):
            self.returncode = code
            self.stdout = stdout
            self.stderr = stderr

    calls = []
    real_run = lw.subprocess.run
    try:
        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            if cmd[:2] == ["hcom", "r"]:
                return FakeResult(1, stderr="mira is still active -- run hcom kill mira first")
            return FakeResult(0)

        lw.subprocess.run = fake_run
        assert lw.send_nudge("claude-lab-mira") is True
    finally:
        lw.subprocess.run = real_run

    assert len(calls) == 3
    assert calls[1][:6] == ["hcom", "r", "claude-lab-mira", "--terminal", "wezterm-tab", "--go"]
    assert calls[2][:4] == ["hcom", "send", "@claude-lab-mira", "--intent"]
    assert lw.NUDGE_PROMPT in calls[2][-1]


def test_send_nudge_active_session_fallback_failure_returns_false():
    import limit_watcher as lw

    class FakeResult:
        def __init__(self, code=0, stdout="", stderr=""):
            self.returncode = code
            self.stdout = stdout
            self.stderr = stderr

    calls = []
    real_run = lw.subprocess.run
    try:
        def fake_run(cmd, **kwargs):
            calls.append(cmd)
            if cmd[:2] == ["hcom", "r"]:
                return FakeResult(1, stderr="target is still active")
            if len(calls) == 3:
                return FakeResult(1, stderr="send failed")
            return FakeResult(0)

        lw.subprocess.run = fake_run
        assert lw.send_nudge("claude-lab-mira") is False
    finally:
        lw.subprocess.run = real_run

    assert len(calls) == 3


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"{len(tests)} limit_watcher tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
