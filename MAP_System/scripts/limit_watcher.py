#!/usr/bin/env python3
"""Limit watcher: auto-resume agents after usage-limit resets (TASK-080).

Deterministic polling loop, no LLM inference. Implements the automation half
of notes/limit-exhaustion-protocol.md:

- Reads agents/status.json. Any agent with status "standby" and reason
  "out_of_tokens" whose resume_after timestamp has passed gets one visible
  resume nudge via `hcom r <name> --terminal wezterm-tab --go`.
- One nudge per agent per resume_after value: repeated polls never spawn the
  same resume twice (spawn-loop guard).
- Unparseable resume_after values are reported once as a durable BLOCKED
  event and then skipped -- the watcher never guesses a reset time.
- Silent-stop detection: an agent that was live on hcom, disappears, and
  never updated status.json gets a durable BLOCKED event so a peer or the
  operator can investigate.

State lives in agents/limit-watcher-state.json. Events append to
events/events.jsonl in the canonical shape. The watcher only reads
status.json; it never writes another agent's status entry.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATUS_FILE = ROOT / "agents" / "status.json"
STATE_FILE = ROOT / "agents" / "limit-watcher-state.json"
EVENT_LOG = ROOT / "events" / "events.jsonl"
TASK_ID = "TASK-080"
SENDER = "limit-watcher"

NUDGE_PROMPT = (
    "Your usage-limit window has reset (limit watcher nudge, TASK-080). "
    "Read MAP_System/handoffs/ for your latest handoff or STATE_SNAPSHOT, "
    "check MAP_System/agents/status.json, set yourself back to available, "
    "and resume your in-flight work."
)


def parse_resume_after(value):
    """ISO-8601 string -> aware datetime, or None if not parseable.

    Naive timestamps are treated as local time (agents write wall-clock
    times from the limit message). Free-text values return None -- the
    watcher never guesses.
    """
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
    """Pure decision: which agents are due a resume nudge right now.

    Returns (nudges, unparseable) where nudges is a list of
    (agent, resume_after_str) and unparseable lists agents whose
    resume_after could not be read as a timestamp (reported once).
    """
    nudges = []
    unparseable = []
    nudged = state.get("nudged", {})
    warned = state.get("warned_unparseable", {})
    agents = status_data.get("agents", {})
    for name, entry in sorted(agents.items()):
        if entry.get("status") != "standby":
            continue
        if entry.get("reason") != "out_of_tokens":
            continue
        raw = entry.get("resume_after")
        parsed = parse_resume_after(raw)
        if parsed is None:
            if warned.get(name) != raw:
                unparseable.append((name, raw))
            continue
        if now < parsed:
            continue
        if nudged.get(name) == raw:
            continue  # already nudged for this window
        nudges.append((name, raw))
    return nudges, unparseable


def detect_silent_stops(prev_live, current_live, status_data, already_reported):
    """Pure decision: agents that vanished from hcom without updating status.

    An agent is a silent stop if it was live last poll, is gone now, and
    status.json still claims it is available. Reported once per disappearance.
    """
    stops = []
    agents = status_data.get("agents", {})
    for name in sorted(set(prev_live) - set(current_live)):
        entry = agents.get(name, {})
        if entry.get("status") not in (None, "available"):
            continue  # it recorded standby/blocked properly; not silent
        if name in already_reported:
            continue
        stops.append(name)
    return stops


def append_event(event_type, summary, artifact_paths=None, dry_run=False):
    event = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "type": event_type,
        "task_id": TASK_ID,
        "sender": SENDER,
        "summary": summary,
        "artifact_paths": artifact_paths or [],
    }
    if dry_run:
        print(f"[dry-run] event: {json.dumps(event)}")
        return
    with EVENT_LOG.open("a") as fh:
        fh.write(json.dumps(event) + "\n")


def hcom_live_agents():
    """Names currently visible to hcom; [] if none; None only if hcom failed.

    The distinction matters: a successful empty list means every previously
    live agent is gone -- exactly when silent-stop detection is most needed.
    Only genuine hcom failure (missing binary, timeout, nonzero exit) returns
    None and skips the check.
    """
    try:
        out = subprocess.run(
            ["hcom", "list", "--names"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    return [line.strip() for line in out.stdout.splitlines() if line.strip()]


def send_nudge(agent, dry_run=False):
    """Announce, then resume the agent in a visible terminal tab."""
    announce = [
        "hcom", "send", f"@{agent}", "--intent", "inform",
        "--name", SENDER, "--",
        f"!NOTE limit watcher: your resume_after window has passed; resuming you now (TASK-080).",
    ]
    resume = [
        "hcom", "r", agent,
        "--terminal", "wezterm-tab",  # operator visibility rule: never headless
        "--go",
        "--hcom-prompt", NUDGE_PROMPT,
    ]
    if dry_run:
        print(f"[dry-run] would run: {' '.join(announce)}")
        print(f"[dry-run] would run: {' '.join(resume)}")
        return True
    subprocess.run(announce, capture_output=True, text=True, timeout=30)
    result = subprocess.run(resume, capture_output=True, text=True, timeout=120)
    return result.returncode == 0


def load_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"nudged": {}, "warned_unparseable": {}, "silent_reported": [], "last_live": []}


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
    now = datetime.now().astimezone()

    nudges, unparseable = decide_nudges(status_data, state, now)
    for agent, raw in unparseable:
        append_event(
            "BLOCKED",
            f"limit watcher: {agent} is out_of_tokens but resume_after ({raw!r}) is not a parseable timestamp; cannot schedule auto-resume. Update agents/status.json with an ISO-8601 time.",
            dry_run=dry_run,
        )
        state.setdefault("warned_unparseable", {})[agent] = raw
    for agent, raw in nudges:
        ok = send_nudge(agent, dry_run=dry_run)
        state.setdefault("nudged", {})[agent] = raw
        append_event(
            "PROGRESS",
            f"limit watcher: resume window passed for {agent} (resume_after {raw}); visible resume nudge {'sent' if ok else 'FAILED'} via hcom r --terminal wezterm-tab.",
            dry_run=dry_run,
        )

    live = hcom_live_agents()
    if live is not None:
        stops = detect_silent_stops(
            state.get("last_live", []), live, status_data,
            set(state.get("silent_reported", [])),
        )
        for agent in stops:
            append_event(
                "BLOCKED",
                f"limit watcher: {agent} disappeared from hcom without updating agents/status.json (possible silent limit hit or crash). A peer or operator should check for a handoff and set its status.",
                dry_run=dry_run,
            )
            state.setdefault("silent_reported", []).append(agent)
        # forget reports for agents that came back
        state["silent_reported"] = [
            a for a in state.get("silent_reported", []) if a not in live
        ]
        state["last_live"] = live

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
    print(f"limit watcher started: interval={args.interval}s status={STATUS_FILE}")
    while True:
        poll_once(dry_run=args.dry_run)
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
