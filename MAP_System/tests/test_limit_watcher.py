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
    """Regression (TASK-080 review finding 1): a successful empty hcom list
    must return [], not None, so silent-stop detection still runs when ALL
    previously live agents have vanished."""
    import limit_watcher as lw

    class FakeResult:
        def __init__(self, code, stdout):
            self.returncode = code
            self.stdout = stdout

    real_run = lw.subprocess.run
    try:
        lw.subprocess.run = lambda *a, **k: FakeResult(0, "")
        assert lw.hcom_live_agents() == []  # empty success -> data
        lw.subprocess.run = lambda *a, **k: FakeResult(0, "rose\nlimo\n")
        assert lw.hcom_live_agents() == ["rose", "limo"]
        lw.subprocess.run = lambda *a, **k: FakeResult(1, "")
        assert lw.hcom_live_agents() is None  # failure -> None
    finally:
        lw.subprocess.run = real_run
    # and the all-vanished scenario produces stops end-to-end
    st = status(rose={"status": "available"}, limo={"status": "available"})
    assert detect_silent_stops(["rose", "limo"], [], st, set()) == ["limo", "rose"]


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print(f"PASS {t.__name__}")
    print(f"{len(tests)} limit_watcher tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
