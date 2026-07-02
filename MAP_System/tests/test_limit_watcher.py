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


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"{len(tests)} limit_watcher tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
