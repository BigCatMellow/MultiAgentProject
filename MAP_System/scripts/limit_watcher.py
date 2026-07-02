#!/usr/bin/env python3
"""Rise & Shine (RnS) limit watcher: auto-resume agents after usage limits.

v1 (TASK-080): nudge agents whose agents/status.json records out_of_tokens
with a passed ISO-8601 resume_after. One nudge per window, visible tabs only.

v2 (TASK-083, after the 2026-07-02 overnight incident): sessions usually hit
the wall with NO final turn -- they never write a status record -- and hcom
keeps listing the stopped session, so absence-based detection never fires.
v2 therefore:

- classifies liveness from `hcom list --json` status + status_age_seconds
  (a dead session stops updating; its age grows unbounded even while listed);
- opens an "incident" for any previously-live agent that goes not-live with
  no deliberate status.json record;
- tries to extract the actual reset time from the session transcript tail
  (the limit message lands there); if found, schedules the nudge for then;
- otherwise probe-resumes on a capped backoff schedule spanning the 5h
  window, giving up loudly after the last probe.

All resumes are visible (`hcom r <name> --terminal wezterm-tab --go`),
never headless. State: agents/limit-watcher-state.json. Events: canonical
shape in events/events.jsonl.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_FILE = ROOT / "agents" / "status.json"
STATE_FILE = ROOT / "agents" / "limit-watcher-state.json"
EVENT_LOG = ROOT / "events" / "events.jsonl"
TASK_ID = "TASK-083"
SENDER = "limit-watcher"

LIVE_STATUSES = {"active", "listening", "waiting", "blocked"}
STALE_AGE_SECONDS = 1800  # status unchanged this long => presumed dead
PROBE_SCHEDULE_MINUTES = [15, 45, 90, 150, 240, 330]  # capped backoff per incident
TRANSCRIPT_TAIL_BYTES = 65536
CHECKIN_IDLE_SECONDS = 7200  # 2h live-but-idle with no claim/declaration => check-in
CHECKIN_SAFE_STATUSES = {"listening"}  # ONLY these hcom states are check-in eligible:
# blocked/waiting sessions are stuck on prompts or dependencies, not drifting
# (TASK-084 review finding 1)
STANDBY_REASONS = {"awaiting_work"}  # declared idle: never check-in-nudged
CHECKIN_TASK_ID = "TASK-084"  # check-in events attribute here, not to the RnS incident task

NUDGE_PROMPT = (
    "Rise & Shine (RnS limit watcher, TASK-083): your session appears to have "
    "hit a usage limit and may have reset. Read MAP_System/handoffs/ for your "
    "latest handoff or STATE_SNAPSHOT, check MAP_System/agents/status.json, "
    "set yourself back to available, and resume your in-flight work. If you "
    "are still rate-limited, simply stop; the watcher will retry later."
)


# ---------------------------------------------------------------- v1 logic

def parse_resume_after(value):
    """ISO-8601 string -> aware datetime, or None. Free text is never guessed."""
    if not value or not isinstance(value, str):
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed


def decide_nudges(status_data, state, now):
    """Recorded-reset path: agents due a resume per their own status entry."""
    nudges = []
    unparseable = []
    nudged = state.get("nudged", {})
    warned = state.get("warned_unparseable", {})
    for name, entry in sorted(status_data.get("agents", {}).items()):
        if entry.get("status") != "standby" or entry.get("reason") != "out_of_tokens":
            continue
        raw = entry.get("resume_after")
        parsed = parse_resume_after(raw)
        if parsed is None:
            if warned.get(name) != raw:
                unparseable.append((name, raw))
            continue
        if now < parsed or nudged.get(name) == raw:
            continue
        nudges.append((name, raw))
    return nudges, unparseable


def detect_silent_stops(prev_live, current_live, status_data, already_reported):
    """v1 pure helper, retained for compatibility/tests. v2 incidents subsume it."""
    stops = []
    agents = status_data.get("agents", {})
    for name in sorted(set(prev_live) - set(current_live)):
        entry = agents.get(name, {})
        if entry.get("status") not in (None, "available"):
            continue
        if name in already_reported:
            continue
        stops.append(name)
    return stops


# ---------------------------------------------------------------- v2 logic

def classify_live(entry):
    """An hcom agent entry counts as live if its status is a live state AND
    its session process still exists.

    `process_bound` is the authoritative signal when present (TASK-084): an
    idle-but-alive agent can sit listening for hours (check-in territory,
    not incident territory), while a dead session keeps its last status with
    the process gone. When hcom doesn't report process_bound, fall back to
    the staleness heuristic from the overnight incident (TASK-083): a status
    unchanged for 30+ minutes is presumed dead."""
    if entry.get("status") not in LIVE_STATUSES:
        return False
    bound = entry.get("process_bound")
    if bound is not None:
        return bool(bound)
    age = entry.get("status_age_seconds")
    if isinstance(age, (int, float)) and age > STALE_AGE_SECONDS:
        return False
    return True


def detect_presumed_down(prev_live, snapshot, status_data, incidents):
    """Previously-live agents now not-live, with no deliberate status.json
    record and no open incident. Absence and stale-but-listed both count."""
    down = []
    agents = status_data.get("agents", {})
    live_now = {n for n, e in snapshot.items() if classify_live(e)}
    for name in sorted(set(prev_live) - live_now):
        entry = agents.get(name, {})
        if entry.get("reason"):  # deliberately recorded (out_of_tokens etc.)
            continue
        if name in incidents:
            continue
        down.append(name)
    return down


_RESET_PATTERNS = [
    # "resets 3pm", "resets at 3:30 pm", "reset at 11am"
    re.compile(r"reset[s]?\s*(?:at\s*)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)", re.IGNORECASE),
    # "resets at 15:00", "reset 09:30"
    re.compile(r"reset[s]?\s*(?:at\s*)?(\d{1,2}):(\d{2})(?!\s*(?:am|pm))", re.IGNORECASE),
]


def parse_reset_time_from_text(text, now):
    """Find the LAST limit-reset mention and convert to the next occurrence.
    Returns aware datetime or None. Never raises."""
    best = None
    for pat in _RESET_PATTERNS:
        for m in pat.finditer(text):
            best = m
    if best is None:
        return None
    try:
        hour = int(best.group(1))
        minute = int(best.group(2) or 0)
        ampm = (best.group(3) or "").lower() if best.lastindex >= 3 else ""
        if ampm == "pm" and hour != 12:
            hour += 12
        elif ampm == "am" and hour == 12:
            hour = 0
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            return None
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate
    except (ValueError, IndexError):
        return None


def read_transcript_reset(path, now):
    """Tail-read a session transcript for a reset time. Bounded, best-effort."""
    try:
        p = Path(path)
        size = p.stat().st_size
        with p.open("rb") as fh:
            fh.seek(max(0, size - TRANSCRIPT_TAIL_BYTES))
            text = fh.read().decode("utf-8", errors="replace")
    except OSError:
        return None
    return parse_reset_time_from_text(text, now)


def probe_action(incident, now):
    """Pure: what should happen for an open incident right now?
    Returns 'wait' | 'nudge' | 'give_up'.

    Backoff anchoring (TASK-083 review finding 1): retries after a
    scheduled-reset nudge anchor to the reset nudge time, NOT detected_at —
    otherwise all earlier backoff slots are already overdue the moment the
    reset nudge fires, and consecutive polls burn probes back-to-back."""
    reset_at = parse_resume_after(incident.get("reset_at"))
    if reset_at is not None:
        if now < reset_at:
            return "wait"
        if not incident.get("reset_nudged"):
            return "nudge"
    probes = incident.get("probes_sent", 0)
    if probes >= len(PROBE_SCHEDULE_MINUTES):
        return "wait" if incident.get("gave_up") else "give_up"
    anchor = parse_resume_after(incident.get("reset_nudged_at")) \
        or parse_resume_after(incident.get("detected_at"))
    if anchor is None:
        return "give_up"
    due = anchor + timedelta(minutes=PROBE_SCHEDULE_MINUTES[probes])
    return "nudge" if now >= due else "wait"


def decide_checkins(snapshot, status_data, claimed_agents, state, now):
    """Pure (TASK-084 / IDEA-0007): live agents that are neither working a
    claimed task nor declared standby, idle past the check-in threshold.

    Safety boundaries from the idea card: a declared reason of any kind
    suppresses (awaiting_work, out_of_tokens, ...), an IN_PROGRESS claim
    suppresses, non-'available' durable status suppresses, and re-nudges are
    throttled to one per idle window."""
    due = []
    agents = status_data.get("agents", {})
    last_checkins = state.get("checkins", {})
    for name, entry in sorted(snapshot.items()):
        if not classify_live(entry):
            continue  # not live: RnS incident territory, not check-in territory
        if entry.get("status") not in CHECKIN_SAFE_STATUSES:
            continue  # active = working; blocked/waiting = stuck, not drifting
        age = entry.get("status_age_seconds")
        if not isinstance(age, (int, float)) or age < CHECKIN_IDLE_SECONDS:
            continue
        durable = agents.get(name, {})
        if durable.get("reason"):
            continue  # declared standby/limit/blocked/etc.
        if durable.get("status") not in (None, "available"):
            continue
        if name in claimed_agents:
            continue  # owns in-flight claimed work
        last = parse_resume_after(last_checkins.get(name))
        if last is not None and (now - last).total_seconds() < CHECKIN_IDLE_SECONDS:
            continue  # already nudged this window
        due.append(name)
    return due


def claimed_agent_ids():
    """Agents currently holding IN_PROGRESS claims in SQLite; None on failure."""
    try:
        import sqlite3
        con = sqlite3.connect(ROOT / "map.db")
        rows = con.execute(
            "SELECT DISTINCT claimed_by FROM tasks "
            "WHERE status='IN_PROGRESS' AND claimed_by IS NOT NULL").fetchall()
        con.close()
        return {r[0] for r in rows}
    except Exception:
        return None


# ------------------------------------------------------------- side effects

def append_event(event_type, summary, artifact_paths=None, dry_run=False, task_id=None):
    event = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "type": event_type,
        "task_id": task_id or TASK_ID,
        "sender": SENDER,
        "summary": summary,
        "artifact_paths": artifact_paths or [],
    }
    if dry_run:
        print(f"[dry-run] event: {json.dumps(event)}")
        return
    with EVENT_LOG.open("a") as fh:
        fh.write(json.dumps(event) + "\n")


def hcom_snapshot():
    """{name: entry} from `hcom list --json`; {} if genuinely no agents;
    None only when hcom itself fails."""
    try:
        out = subprocess.run(["hcom", "list", "--json"],
                             capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    try:
        data = json.loads(out.stdout)
    except json.JSONDecodeError:
        return None
    snap = {}
    for entry in data if isinstance(data, list) else []:
        name = entry.get("name")
        if name:
            snap[name] = entry
    return snap


def send_nudge(agent, dry_run=False, kind="resume"):
    announce = ["hcom", "send", f"@{agent}", "--intent", "inform", "--name", SENDER,
                "--", f"!NOTE RnS: {kind} nudge for {agent} (TASK-083)."]
    resume = ["hcom", "r", agent, "--terminal", "wezterm-tab", "--go",
              "--hcom-prompt", NUDGE_PROMPT]
    if dry_run:
        print(f"[dry-run] would announce + run: {' '.join(resume)}")
        return True
    subprocess.run(announce, capture_output=True, text=True, timeout=30)
    result = subprocess.run(resume, capture_output=True, text=True, timeout=180)
    return result.returncode == 0


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {}


def save_state(state, dry_run=False):
    if dry_run:
        return
    STATE_FILE.write_text(json.dumps(state, indent=2) + "\n")


def poll_once(dry_run=False):
    try:
        status_data = json.loads(STATUS_FILE.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"warning: cannot read {STATUS_FILE}: {exc}", file=sys.stderr)
        return
    state = load_state()
    state.setdefault("nudged", {})
    state.setdefault("warned_unparseable", {})
    state.setdefault("incidents", {})
    state.setdefault("last_live", [])
    now = datetime.now().astimezone()

    # v1: recorded-reset path
    nudges, unparseable = decide_nudges(status_data, state, now)
    for agent, raw in unparseable:
        append_event("BLOCKED",
            f"RnS: {agent} is out_of_tokens but resume_after ({raw!r}) is not a "
            f"parseable timestamp; cannot schedule auto-resume.", dry_run=dry_run)
        state["warned_unparseable"][agent] = raw
    for agent, raw in nudges:
        ok = send_nudge(agent, dry_run=dry_run, kind="recorded-reset")
        state["nudged"][agent] = raw
        append_event("PROGRESS",
            f"RnS: recorded resume window passed for {agent} (resume_after {raw}); "
            f"visible resume nudge {'sent' if ok else 'FAILED'}.", dry_run=dry_run)

    # v2: presumed-down incidents
    snapshot = hcom_snapshot()
    if snapshot is not None:
        live_now = sorted(n for n, e in snapshot.items() if classify_live(e))

        # agents that rose again: close incidents
        for name in [n for n in state["incidents"] if n in live_now]:
            inc = state["incidents"].pop(name)
            append_event("PROGRESS",
                f"RnS: {name} is live again (incident opened {inc.get('detected_at')}, "
                f"{inc.get('probes_sent', 0)} probe(s) sent). Incident closed.",
                dry_run=dry_run)

        # newly presumed-down agents: open incidents
        for name in detect_presumed_down(state["last_live"], snapshot,
                                         status_data, state["incidents"]):
            entry = snapshot.get(name, {})
            transcript = entry.get("transcript_path")
            reset_at = read_transcript_reset(transcript, now) if transcript else None
            state["incidents"][name] = {
                "detected_at": now.isoformat(timespec="seconds"),
                "reset_at": reset_at.isoformat(timespec="seconds") if reset_at else None,
                "probes_sent": 0, "reset_nudged": False, "gave_up": False,
            }
            append_event("BLOCKED",
                f"RnS: {name} presumed down without a status record (limit hit with "
                f"no final turn, or crash). "
                + (f"Reset time {reset_at.isoformat(timespec='seconds')} found in its "
                   f"transcript; nudge scheduled." if reset_at else
                   f"No reset time found; probing on backoff "
                   f"{PROBE_SCHEDULE_MINUTES} minutes."), dry_run=dry_run)

        # act on open incidents
        for name, inc in state["incidents"].items():
            action = probe_action(inc, now)
            if action == "nudge":
                reset_known = parse_resume_after(inc.get("reset_at")) is not None \
                    and not inc.get("reset_nudged")
                ok = send_nudge(name, dry_run=dry_run,
                                kind="scheduled-reset" if reset_known else "probe")
                if reset_known:
                    inc["reset_nudged"] = True
                    inc["reset_nudged_at"] = now.isoformat(timespec="seconds")
                else:
                    inc["probes_sent"] = inc.get("probes_sent", 0) + 1
                append_event("PROGRESS",
                    f"RnS: {'scheduled-reset' if reset_known else 'probe'} nudge "
                    f"{'sent' if ok else 'FAILED'} for {name} "
                    f"(probes so far: {inc.get('probes_sent', 0)}).", dry_run=dry_run)
            elif action == "give_up":
                inc["gave_up"] = True
                append_event("BLOCKED",
                    f"RnS: giving up on {name} after {inc.get('probes_sent', 0)} probes "
                    f"across the backoff window. Operator or peer attention needed.",
                    dry_run=dry_run)

        state["last_live"] = live_now

        # check-in path (TASK-084): message-only, never a spawn
        claimed = claimed_agent_ids()
        if claimed is not None:
            state.setdefault("checkins", {})
            for name in decide_checkins(snapshot, status_data, claimed, state, now):
                msg = (f"!NOTE RnS check-in: you've been idle "
                       f"{int(snapshot[name].get('status_age_seconds', 0) // 3600)}h+ with no "
                       f"claimed task and no standby declaration. Is there something you "
                       f"should be doing? If your queue is genuinely empty, run: python3 "
                       f"MAP_System/scripts/declare_standby.py {name}")
                if dry_run:
                    print(f"[dry-run] would check-in nudge {name}: {msg}")
                else:
                    subprocess.run(["hcom", "send", f"@{name}", "--intent", "request",
                                    "--name", SENDER, "--", msg],
                                   capture_output=True, text=True, timeout=30)
                state["checkins"][name] = now.isoformat(timespec="seconds")
                append_event("PROGRESS",
                    f"RnS check-in nudge sent to {name}: live but idle past "
                    f"{CHECKIN_IDLE_SECONDS // 3600}h with no claim and no standby "
                    f"declaration.", dry_run=dry_run, task_id=CHECKIN_TASK_ID)

    save_state(state, dry_run=dry_run)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--interval", type=int, default=60, help="poll seconds")
    parser.add_argument("--once", action="store_true", help="single poll, then exit")
    parser.add_argument("--dry-run", action="store_true", help="print actions, write nothing")
    args = parser.parse_args()

    if args.once:
        poll_once(dry_run=args.dry_run)
        return 0
    print(f"RnS limit watcher started: interval={args.interval}s status={STATUS_FILE}")
    while True:
        poll_once(dry_run=args.dry_run)
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
