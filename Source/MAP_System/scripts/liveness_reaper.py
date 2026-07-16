#!/usr/bin/env python3
"""Liveness/reaper implementation for MAP 6.13 Wave 2.5 (TASK-150 spec, TASK-158 build).

Computes per-agent liveness state from agents/status.json, optional hcom
status data, and map.db task claims; applies the timeout policy defaults
from map-liveness-reaper-spec.md; and implements the action ladder
(suspect -> nudge -> reclaim -> dead-letter -> broken) as accounting-only
by default. Reclaim reuses the existing db/claims.py `expire_leases()`
helper rather than reimplementing claim-clearing logic, per the spec's
"reaper writes must go through sanctioned SQLite helpers" rule.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

try:
    from MAP_System.scripts.event_trace import add_trace_fields
except ModuleNotFoundError:  # direct script execution
    from event_trace import add_trace_fields

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATUS = ROOT / "agents" / "status.json"
DEFAULT_DB = ROOT / "map.db"
DEFAULT_EVENT_LOG = ROOT / "events" / "events.jsonl"
DEFAULT_SNAPSHOT_MD = ROOT / "shared" / "liveness-state.md"
DEFAULT_DEAD_LETTER_LOG = ROOT / "dead_letters" / "dead_letters.jsonl"

SENDER = "liveness-reaper"
TASK_ID = "TASK-158"

LIVE_HCOM_STATUSES = {"active", "listening", "waiting", "blocked"}
STALE_AGE_SECONDS = 1800
CHECKIN_IDLE_SECONDS = 7200
WORK_NUDGE_SECONDS = 1800
WORK_NUDGE_MIN_IDLE = 120
STANDBY_REASONS = {"awaiting_work"}

STATES = {"alive", "working", "blocked", "idle", "suspect", "broken", "standby"}


@dataclass
class LivenessRecord:
    agent_id: str
    last_seen: str | None
    active_task: str | None
    lane: str
    state: str
    state_since: str
    stale_after: str | None
    evidence: str


def _now_iso(now: datetime) -> str:
    return now.strftime("%Y-%m-%dT%H:%M:%SZ")


def classify_state(
    agent_id: str,
    status_entry: dict | None,
    hcom_entry: dict | None,
    claimed_task_row: tuple[str, str] | None,
    now: datetime,
) -> LivenessRecord:
    """Pure classification: no I/O, fully unit-testable.

    claimed_task_row: (task_id, status) for the task this agent currently
    claims IN_PROGRESS, or None.
    """
    status_entry = status_entry or {}
    declared_status = status_entry.get("status")
    declared_reason = status_entry.get("reason")

    active_task = claimed_task_row[0] if claimed_task_row else None

    if declared_status == "standby" or declared_reason in STANDBY_REASONS:
        return LivenessRecord(
            agent_id=agent_id,
            last_seen=None,
            active_task=active_task,
            lane="service" if agent_id in {"map-task", "reconcile", "langgraph-runner", "limit-watcher"} else "core",
            state="standby",
            state_since=_now_iso(now),
            stale_after=None,
            evidence=f"status:{declared_status or declared_reason}",
        )

    hcom_status = (hcom_entry or {}).get("status")
    # status_age_seconds: freshness of hcom's own last report (small = hcom
    # confirms this agent is alive right now; large = hcom hasn't heard from
    # it in a while = presumed dead, per limit_watcher.py's STALE_AGE_SECONDS
    # semantics). idle_seconds: a SEPARATE clock -- how long since the agent
    # last had a task claim or declared activity. These are independent: an
    # agent can report a fresh "listening" ping every few seconds while still
    # having gone hours without claiming any work. Conflating the two into
    # one field made the `idle` state unreachable (its 7200s threshold is
    # larger than `suspect`'s 1800s threshold on the same clock) -- caught by
    # this task's own test suite before submission.
    status_age_seconds = (hcom_entry or {}).get("status_age_seconds")
    idle_seconds = (hcom_entry or {}).get("idle_seconds")
    last_seen = (hcom_entry or {}).get("last_seen")

    if hcom_status in LIVE_HCOM_STATUSES:
        if status_age_seconds is not None and status_age_seconds > STALE_AGE_SECONDS:
            return LivenessRecord(
                agent_id=agent_id,
                last_seen=last_seen,
                active_task=active_task,
                lane="core",
                state="suspect",
                state_since=_now_iso(now),
                stale_after=None,
                evidence=f"hcom:{hcom_status}_but_stale_{status_age_seconds}s",
            )
        if active_task:
            return LivenessRecord(
                agent_id=agent_id,
                last_seen=last_seen,
                active_task=active_task,
                lane="core",
                state="working" if hcom_status in {"active", "listening"} else "blocked",
                state_since=_now_iso(now),
                stale_after=None,
                evidence=f"hcom:{hcom_status};task:IN_PROGRESS",
            )
        if hcom_status == "blocked":
            return LivenessRecord(
                agent_id=agent_id,
                last_seen=last_seen,
                active_task=None,
                lane="core",
                state="blocked",
                state_since=_now_iso(now),
                stale_after=None,
                evidence="hcom:blocked",
            )
        if idle_seconds is not None and idle_seconds > CHECKIN_IDLE_SECONDS:
            return LivenessRecord(
                agent_id=agent_id,
                last_seen=last_seen,
                active_task=None,
                lane="core",
                state="idle",
                state_since=_now_iso(now),
                stale_after=None,
                evidence=f"hcom:{hcom_status};idle_{idle_seconds}s",
            )
        return LivenessRecord(
            agent_id=agent_id,
            last_seen=last_seen,
            active_task=None,
            lane="core",
            state="alive",
            state_since=_now_iso(now),
            stale_after=None,
            evidence=f"hcom:{hcom_status}",
        )

    # No live hcom signal at all (hcom_status is None, or an unrecognized
    # value hcom emits for a dead/unreachable session). A claimed task with
    # zero liveness visibility is the worst case -- worse than a merely idle
    # agent -- regardless of what status.json still declares, since that
    # file can lag real session state (see agents/README.md's identity-kind
    # caveat and REPAIR history on stale status.json entries).
    if active_task:
        return LivenessRecord(
            agent_id=agent_id,
            last_seen=last_seen,
            active_task=active_task,
            lane="core",
            state="broken",
            state_since=_now_iso(now),
            stale_after=None,
            evidence=f"status:{declared_status};task:IN_PROGRESS;no_hcom_data",
        )
    return LivenessRecord(
        agent_id=agent_id,
        last_seen=last_seen,
        active_task=None,
        lane="core",
        state="suspect",
        state_since=_now_iso(now),
        stale_after=None,
        evidence=f"status:{declared_status};no_hcom_data",
    )


def load_status(path: Path = DEFAULT_STATUS) -> dict:
    return json.loads(path.read_text(encoding="utf-8")).get("agents", {})


def normalize_hcom_status(raw: dict | list) -> dict[str, dict]:
    """Accepts either shape of hcom status data and returns the agent-keyed
    dict `classify_state`/`build_snapshot` expect.

    `hcom list --json` actually returns a LIST of per-session records keyed
    by `name` (e.g. `claude-lab-zera`), not an agent-keyed object -- passing
    that raw list straight through previously crashed with
    `AttributeError: 'list' object has no attribute 'get'` (TASK-175's
    runtime-exercise audit reproduced and reported this; confirmed here by
    reproducing it again before this fix).

    Still accepts an already agent-keyed dict unchanged, for callers/tests
    that construct fixtures directly in that shape.
    """
    if isinstance(raw, dict):
        return raw
    if not isinstance(raw, list):
        raise TypeError(f"hcom status data must be a dict or list, got {type(raw).__name__}")

    normalized: dict[str, dict] = {}
    for record in raw:
        agent_id = record.get("name") or record.get("base_name")
        if not agent_id:
            continue
        normalized[agent_id] = {
            "status": record.get("status"),
            "status_age_seconds": record.get("status_age_seconds"),
            "last_seen": record.get("status_detail") or record.get("description"),
            # hcom's raw record has no direct "idle_seconds" concept; left
            # absent here rather than guessed, so classify_state's existing
            # idle-detection path (which requires an explicit value) is not
            # silently fed a made-up number.
        }
    return normalized


def load_claimed_tasks(db_path: Path = DEFAULT_DB) -> dict[str, tuple[str, str]]:
    """Map agent_id -> (task_id, status) for every IN_PROGRESS claim."""
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT claimed_by, task_id, status FROM tasks WHERE status = 'IN_PROGRESS' AND claimed_by IS NOT NULL"
        ).fetchall()
    finally:
        conn.close()
    result: dict[str, tuple[str, str]] = {}
    for claimed_by, task_id, status in rows:
        result[claimed_by] = (task_id, status)
    return result


def build_snapshot(
    status_path: Path = DEFAULT_STATUS,
    hcom_status_by_agent: dict[str, dict] | None = None,
    db_path: Path = DEFAULT_DB,
    now: datetime | None = None,
) -> list[LivenessRecord]:
    now = now or datetime.now(timezone.utc)
    status_agents = load_status(status_path)
    claimed = load_claimed_tasks(db_path)
    hcom_status_by_agent = hcom_status_by_agent or {}

    records = []
    for agent_id, status_entry in status_agents.items():
        hcom_entry = hcom_status_by_agent.get(agent_id)
        claimed_row = claimed.get(agent_id)
        records.append(classify_state(agent_id, status_entry, hcom_entry, claimed_row, now))
    return sorted(records, key=lambda r: r.agent_id)


def render_snapshot_markdown(records: list[LivenessRecord], now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    lines = [
        "<!-- hpom: file: shared/liveness-state.md -->",
        "<!-- hpom: project: MAP -->",
        "<!-- hpom: state_owner: command-center -->",
        "<!-- hpom: status: CURRENT -->",
        f"<!-- hpom: last_verified: {now.strftime('%Y-%m-%d')} -->",
        "<!-- hpom: verified_against: TASK-158 liveness_reaper.py -->",
        "<!-- hpom: confidence: MEDIUM -->",
        "<!-- hpom: supersedes: NONE -->",
        "<!-- hpom: superseded_by: NONE -->",
        "",
        "# MAP Liveness State",
        "",
        f"Generated {_now_iso(now)} by `scripts/liveness_reaper.py`. Read-only",
        "snapshot -- mission-control and other consumers should treat this as",
        "derived state, not a second source of truth for agent status.",
        "",
        "| Agent | State | Active Task | Lane | Evidence |",
        "|---|---|---|---|---|",
    ]
    for r in records:
        lines.append(f"| {r.agent_id} | {r.state} | {r.active_task or '-'} | {r.lane} | {r.evidence} |")
    lines.append("")
    return "\n".join(lines)


def append_event(
    event_type: str,
    summary: str,
    task_id: str = TASK_ID,
    artifact_paths: list[str] | None = None,
    action: str | None = None,
    target: str | None = None,
    event_log: Path = DEFAULT_EVENT_LOG,
) -> None:
    event = {
        "created_at": _now_iso(datetime.now(timezone.utc)),
        "type": event_type,
        "task_id": task_id,
        "sender": SENDER,
        "summary": summary,
        "artifact_paths": artifact_paths or [],
    }
    if action:
        event["actor"] = SENDER
        event["action"] = action
    if target:
        event["target"] = target
    add_trace_fields(event, actor=SENDER if action else None, action=action, target=target)
    with open(event_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


class ReclaimMirrorError(RuntimeError):
    """Raised when a real reclaim leaves SQLite and file mirrors divergent."""


def _export_and_validate_mirrors(
    repo_root: Path,
    db_path: Path | None = None,
    mirror_root: Path | None = None,
) -> None:
    """Run the same export -> validate sequence the spec and TASK-158's
    review require after any real reclaim: SQLite state must be reflected
    in the file mirrors before the reaper reports success, not left to an
    unrelated later export to catch.

    db_path/mirror_root let tests point this at an isolated fixture copy
    instead of canonical MAP_System/map.db and tasks/workflow/ -- reclaim
    and dead-letter replay must never be chaos-tested against real state.
    """
    export_cmd = [sys.executable, str(ROOT / "migration" / "export_to_files.py")]
    validate_cmd = [sys.executable, str(ROOT / "scripts" / "validate_task_mirrors.py")]
    if db_path is not None:
        export_cmd += ["--db", str(db_path)]
        validate_cmd += ["--db", str(db_path)]
    if mirror_root is not None:
        export_cmd += ["--output-dir", str(mirror_root)]
        validate_cmd += ["--root", str(mirror_root)]

    export = subprocess.run(export_cmd, cwd=repo_root, text=True, capture_output=True, check=False)
    if export.returncode != 0:
        raise ReclaimMirrorError(f"export_to_files.py failed: {export.stderr.strip()}")
    validate = subprocess.run(validate_cmd, cwd=repo_root, text=True, capture_output=True, check=False)
    if validate.returncode != 0:
        raise ReclaimMirrorError(f"validate_task_mirrors.py failed after reclaim: {validate.stdout.strip()}")


def reclaim_stale_claims(
    db_path: Path = DEFAULT_DB,
    dry_run: bool = True,
    repo_root: Path | None = None,
    mirror_root: Path | None = None,
    event_log: Path = DEFAULT_EVENT_LOG,
) -> list[str]:
    """Reclaim tasks whose lease has expired, via the existing sanctioned helper.

    Returns the list of reclaimed task IDs. In dry_run mode (default),
    only reports what WOULD be reclaimed without calling expire_leases().

    A real (non-dry-run) reclaim is followed by export_to_files.py and
    validate_task_mirrors.py, per TASK-158's review finding: SQLite and
    file mirrors must not be left divergent after a reaper action.
    ReclaimMirrorError is raised (not swallowed) if that post-check fails,
    so a caller cannot silently report success on a half-applied reclaim.

    event_log must be overridden to an isolated path in any fixture-backed
    test -- the previous absence of this parameter caused test runs to
    append fixture task IDs into canonical events.jsonl (TASK-158 rereview
    finding; see REPAIR-0007).
    """
    sys.path.insert(0, str(ROOT.parent))
    from MAP_System.db.claims import expire_leases

    if dry_run:
        conn = sqlite3.connect(db_path)
        try:
            rows = conn.execute(
                """
                SELECT task_id FROM tasks
                WHERE status = 'IN_PROGRESS' AND claimed_by IS NOT NULL
                  AND lease_expires_at IS NOT NULL AND lease_expires_at < datetime('now')
                """
            ).fetchall()
        finally:
            conn.close()
        return [r[0] for r in rows]

    reclaimed = list(expire_leases(db_path=db_path))
    if reclaimed:
        _export_and_validate_mirrors(repo_root or ROOT.parent, db_path=db_path, mirror_root=mirror_root)
    for task_id in reclaimed:
        append_event(
            "PROGRESS",
            f"Liveness reaper reclaimed expired lease for {task_id} (mirrors exported and validated)",
            action="reclaim",
            target=task_id,
            event_log=event_log,
        )
    return reclaimed


class DeadLetterReplayError(RuntimeError):
    """Raised when a dead-lettered task cannot be safely replayed to READY."""


REPLAYABLE_STATUSES = {"IN_PROGRESS", "READY"}


def _dead_letter_path_repr(dead_letter_log: Path) -> str:
    return (
        str(dead_letter_log.relative_to(ROOT.parent))
        if dead_letter_log.is_relative_to(ROOT.parent)
        else str(dead_letter_log)
    )


def dead_letter_task(
    task_id: str,
    agent_id: str,
    reason: str,
    dead_letter_log: Path = DEFAULT_DEAD_LETTER_LOG,
    event_log: Path = DEFAULT_EVENT_LOG,
) -> str:
    """Append a dead-letter record. Interim minimal store -- TASK-161's
    resilience work (scripts/dead_letter_queue.py) is the canonical
    dead-letter queue; this liveness-specific record links to it by
    task_id/agent_id and should be folded in once that lands, not
    duplicated as a second permanent store.

    The record documents its own replay_command so a future agent (or
    TASK-161's queue) does not need to rediscover how to requeue it --
    per TASK-158's review finding, replay must be a supported transition,
    not a hand-edit of task_graph.json.
    """
    dead_letter_log.parent.mkdir(parents=True, exist_ok=True)
    dead_letter_id = f"DL-{uuid.uuid4().hex[:8]}"
    record = {
        "dead_letter_id": dead_letter_id,
        "task_id": task_id,
        "agent_id": agent_id,
        "detected_at": _now_iso(datetime.now(timezone.utc)),
        "reason": reason,
        "replay_status": "pending",
        "replay_command": (
            f"python3 MAP_System/scripts/liveness_reaper.py "
            f"--replay-dead-letter {dead_letter_id}"
        ),
        "source": "liveness_reaper",
    }
    with open(dead_letter_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    append_event(
        "PROGRESS",
        f"Liveness reaper dead-lettered {task_id} (agent {agent_id}): {reason}",
        action="dead_letter",
        target=task_id,
        artifact_paths=[_dead_letter_path_repr(dead_letter_log)],
        event_log=event_log,
    )
    return dead_letter_id


def _read_dead_letter_records(dead_letter_log: Path) -> list[dict]:
    if not dead_letter_log.exists():
        return []
    return [json.loads(line) for line in dead_letter_log.read_text(encoding="utf-8").splitlines() if line.strip()]


def _latest_dead_letter_status(dead_letter_log: Path, dead_letter_id: str) -> dict | None:
    matching = [r for r in _read_dead_letter_records(dead_letter_log) if r["dead_letter_id"] == dead_letter_id]
    return matching[-1] if matching else None


def replay_dead_letter(
    dead_letter_id: str,
    dead_letter_log: Path = DEFAULT_DEAD_LETTER_LOG,
    db_path: Path = DEFAULT_DB,
    event_log: Path = DEFAULT_EVENT_LOG,
    repo_root: Path | None = None,
    mirror_root: Path | None = None,
) -> dict:
    """Replay a dead-lettered task back to READY through a supported
    transition -- never by hand-editing task_graph.json. Requeues via a
    direct, narrowly-scoped SQLite update (the same shape
    db/claims.py's expire_leases()/release_task() already use: clear
    claimed_by/lease/heartbeat, set status), then exports and validates
    file mirrors before reporting success, exactly like reclaim_stale_claims.

    Raises DeadLetterReplayError if the dead_letter_id is unknown, already
    replayed, or the task is not in a status this replay path is allowed
    to touch (protects against reviving an already-APPROVED/RELEASED task).
    """
    record = _latest_dead_letter_status(dead_letter_log, dead_letter_id)
    if record is None:
        raise DeadLetterReplayError(f"unknown dead_letter_id: {dead_letter_id}")
    if record.get("replay_status") == "replayed":
        raise DeadLetterReplayError(f"{dead_letter_id} was already replayed at a prior run")

    task_id = record["task_id"]
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        row = conn.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,)).fetchone()
        if row is None:
            raise DeadLetterReplayError(f"{task_id} not found in tasks table")
        status = row[0]
        if status not in REPLAYABLE_STATUSES:
            raise DeadLetterReplayError(
                f"{task_id} is {status}, not one of {sorted(REPLAYABLE_STATUSES)} -- "
                "refusing to replay a task that has moved past dead-letter scope"
            )
        if status == "IN_PROGRESS":
            conn.execute(
                """
                UPDATE tasks
                SET status = 'READY', claimed_by = NULL, lease_expires_at = NULL,
                    heartbeat_at = NULL, updated_at = datetime('now')
                WHERE task_id = ?
                """,
                (task_id,),
            )
            conn.commit()
    finally:
        conn.close()

    _export_and_validate_mirrors(repo_root or ROOT.parent, db_path=db_path, mirror_root=mirror_root)

    updated_record = {**record, "replay_status": "replayed", "replayed_at": _now_iso(datetime.now(timezone.utc))}
    with open(dead_letter_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(updated_record) + "\n")
    append_event(
        "PROGRESS",
        f"Liveness reaper replayed dead-letter {dead_letter_id} for {task_id} back to READY",
        action="replay",
        target=task_id,
        artifact_paths=[_dead_letter_path_repr(dead_letter_log)],
        event_log=event_log,
    )
    return updated_record


def circuit_breaker_signal(signal: str, agent_id: str) -> None:
    """Accounting-only signal, per the spec's day-one non-blocking rule."""
    append_event(
        "PROGRESS",
        f"Liveness circuit-breaker signal: {signal} for {agent_id} (accounting-only)",
        action=signal,
        target=agent_id,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status-file", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--snapshot-out", type=Path, default=DEFAULT_SNAPSHOT_MD)
    parser.add_argument("--hcom-json", type=Path, help="File with hcom-derived status per agent_id")
    parser.add_argument("--act", action="store_true", help="Actually reclaim stale leases (default: dry-run/report only)")
    parser.add_argument("--replay-dead-letter", metavar="DEAD_LETTER_ID", help="Replay a dead-lettered task back to READY and exit")
    parser.add_argument("--dead-letter-log", type=Path, default=DEFAULT_DEAD_LETTER_LOG)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.replay_dead_letter:
        result = replay_dead_letter(args.replay_dead_letter, dead_letter_log=args.dead_letter_log, db_path=args.db)
        print(json.dumps(result, indent=2) if args.json else f"Replayed {args.replay_dead_letter}: {result}")
        return 0

    hcom_status = {}
    if args.hcom_json and args.hcom_json.exists():
        hcom_status = normalize_hcom_status(json.loads(args.hcom_json.read_text(encoding="utf-8")))

    records = build_snapshot(args.status_file, hcom_status, args.db)
    markdown = render_snapshot_markdown(records)
    args.snapshot_out.write_text(markdown, encoding="utf-8")

    reclaim_candidates = reclaim_stale_claims(args.db, dry_run=not args.act)

    if args.json:
        print(json.dumps({
            "records": [r.__dict__ for r in records],
            "reclaim_candidates": reclaim_candidates,
            "acted": args.act,
        }, indent=2))
    else:
        for r in records:
            print(f"{r.agent_id}: {r.state} ({r.evidence})")
        print(f"Reclaim candidates: {reclaim_candidates} (acted={args.act})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
