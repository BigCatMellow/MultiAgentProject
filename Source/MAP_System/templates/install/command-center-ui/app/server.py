#!/usr/bin/env python3
"""Local CommandCenterUI app server.

Serves the Studio UI and exposes localhost-only APIs for MAP state and guarded
hcom sends. Uses only Python stdlib so the app can run without dependency
installation.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
from urllib.parse import quote
from urllib.parse import unquote
from urllib.parse import parse_qs, urlparse


PROJECT_DIR = Path(__file__).resolve().parents[1]


def resolve_workspace() -> Path:
    """Find the MAP workspace (the directory containing MAP_System).

    CommandCenterUI used to live nested inside the MultiAgentProject repo, so
    the workspace was a fixed relative-path hop up. It is standalone now, so
    the workspace must be discovered or configured explicitly.
    """
    override = os.environ.get("COMMAND_CENTER_UI_WORKSPACE")
    if override:
        workspace = Path(override).expanduser()
        if not (workspace / "MAP_System").is_dir():
            raise SystemExit(
                f"CommandCenterUI: COMMAND_CENTER_UI_WORKSPACE={override!r} has no "
                "MAP_System directory. Refusing to fall back to discovery when an "
                "explicit workspace is set."
            )
        return workspace.resolve()
    candidates = []
    # Old nested layout: <workspace>/Projects/CommandCenterUI
    candidates.append(PROJECT_DIR.parents[1])
    # Standalone layout: sibling checkout of the canonical repo.
    candidates.append(PROJECT_DIR.parent / "MultiAgentProject")
    candidates.append(Path.home() / "Projects" / "MultiAgentProject")
    for candidate in candidates:
        if (candidate / "MAP_System").is_dir():
            return candidate.resolve()
    raise SystemExit(
        "CommandCenterUI: no MAP workspace found (looked for a MAP_System dir in: "
        + ", ".join(str(c) for c in candidates)
        + "). Set COMMAND_CENTER_UI_WORKSPACE=/path/to/MultiAgentProject and retry."
    )


WORKSPACE = resolve_workspace()
MAP_DIR = WORKSPACE / "MAP_System"
SRC_DIR = PROJECT_DIR / "src"
EVENTS_PATH = MAP_DIR / "events" / "events.jsonl"
TASK_GRAPH_PATH = MAP_DIR / "workflow" / "task_graph.json"
TASKS_DIR = MAP_DIR / "tasks"
AGENTS_STATUS_PATH = MAP_DIR / "agents" / "status.json"

RECIPIENT_RE = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
HCOM_NAME_RE = re.compile(r"^[a-z0-9_]{1,64}$")
INTENTS = {"request", "inform", "ack"}
HCOM_AGENT_NAME = "browser"
HCOM_DB = Path.home() / ".hcom" / "hcom.db"
# External (non-agent) identity chat sends are attributed to. This is the
# operator's established hcom identity; it is sent with `--from`, which hcom
# records as sender_kind=external, so the UI can never impersonate an agent.
OPERATOR_NAME = os.environ.get("COMMAND_CENTER_UI_OPERATOR", "command-center")
MENTION_RE = re.compile(r"(?<![\w@])@([A-Za-z0-9_-]{2,64})")
LAB_LAUNCHER = Path.home() / ".local" / "bin" / "ai-command-center-lab"
LOCAL_GOOSE_LAUNCHER = Path.home() / ".local" / "bin" / "ai-command-center-ollama-goose"
OLLAMA_MODEL_LAUNCHER = Path.home() / ".local" / "bin" / "ai-command-center-ollama-model"
LAB_CLAUDE_LAUNCHER = Path.home() / ".local" / "bin" / "ai-command-center-lab-claude"
LAB_CODEX_LAUNCHER = Path.home() / ".local" / "bin" / "ai-command-center-lab-codex"
WEZTERM_BIN = Path.home() / ".local" / "bin" / "wezterm"
OLLAMA_URL = os.environ.get("COMMAND_CENTER_UI_OLLAMA", "http://127.0.0.1:11434")
SUMMARY_MODEL = os.environ.get("COMMAND_CENTER_UI_SUMMARY_MODEL", "gemma3:4b")
SUMMARY_CACHE_PATH = Path(__file__).resolve().parents[1] / "runtime" / "relay-summaries-v2.json"
SUMMARY_PROMPT = (
    "You are the AI Command Center relay. Rewrite the agent message below for "
    "the human operator in a casual, structured status-card tone.\n\n"
    "Rules:\n"
    "- Preserve the actual facts, names, task IDs, warnings, blockers, and next actions.\n"
    "- Keep exact task IDs and agent names exactly as written, such as TASK-193 or claude-lab-mira.\n"
    "- Do not say work is done unless the source message says it is done.\n"
    "- Do not turn status updates into requests. Only say the operator needs to decide/help/approve if the source explicitly asks the operator.\n"
    "- If the agent is explicitly asking for approval, a decision, or help, make that clear.\n"
    "- Keep file paths only when they are essential; otherwise say the relevant file or script.\n"
    "- Do not include raw hcom relay lines, command echoes, or duplicate subscription lines.\n"
    "- Output 2-5 short lines when there is more than one fact.\n"
    "- Line 1 is a plain-language lead sentence.\n"
    "- Detail lines must use labels like Need:, Done:, Next:, Blocker:, Review:, Tests:, or Refs:.\n"
    "- Use a few '- ' bullet lines only for parallel items that would be hard to read in one sentence.\n"
    "- No markdown fences, no headings, no quotes, no preamble.\n\n"
    "Important: output only the formatted relay text. Do not say you rewrote it, "
    "do not introduce it, and do not wrap it in quotation marks.\n\n"
    "Examples:\n"
    "Raw: TASK-193 submitted after export_to_files completed; validation passed.\n"
    "Relay:\nMira submitted TASK-193 after exporting the files.\nTests: validation passed.\n"
    "Raw: TASK-193 submitted; validation passed. Next I am watching for reviewer approval.\n"
    "Relay:\nNivo submitted TASK-193 and is waiting on reviewer approval.\nTests: validation passed.\n"
    "Raw: !REQ needs operator decision: continue review or find a new reviewer.\n"
    "Relay:\nNivo needs your decision.\nNeed: keep the current review going or assign someone new.\n\n"
    "Message from {sender}: {text}"
)
LAB_TAGS = {"claude-lab", "codex-lab"}
WATCHER_PIDFILE = MAP_DIR / ".locks" / "limit-watcher.pid"
PROJECT_UPDATER_DIR = WORKSPACE / "Projects" / "ProjectUpdater"
PROJECT_UPDATER_APP = PROJECT_UPDATER_DIR / "app" / "index.html"
PROJECT_UPDATER_EXPORT = Path.home() / "Downloads" / "project-updater-status.json"
PROJECT_UPDATER_EMBED_PATH = "/project-updater/"

# MAP runtime health sources (TASK-182). All read-only: route computation,
# validators, and status subcommands only — never build/apply/write commands.
MAP_VENV_PY = MAP_DIR / ".venv" / "bin" / "python"
WATCHER_STATE_PATH = MAP_DIR / "agents" / "limit-watcher-state.json"
MAP_HEALTH_TTL_SECONDS = 20.0
MAP_HEALTH_SCRIPT_TIMEOUT = 25
RNS_SYNC_NOTE_MARKER = "command-center-token-refresh"

OLLAMA_MODEL_USES = {
    "llama3.2:3b": "orientation, summaries, event digests",
    "llama3.2:1b": "tiny summaries, classification, routing hints",
    "qwen2.5-coder:3b": "JSON, schemas, validators, SQLite helper logic",
    "qwen2.5-coder:1.5b": "fast syntax, key, and path checks",
    "gemma3:4b": "acceptance criteria, markdown cleanup, review drafts",
}

BASE_LOCAL_AGENT_DEFS = {
    "ollama-goose": {
        "id": "ollama-goose",
        "name": "ollama: goose",
        "label": "ollama: goose",
        "tool": "ollama",
        "tool_label": "Ollama",
        "model": "Goose",
        "hcom_name": "ollama-goose",
        "launcher": LOCAL_GOOSE_LAUNCHER,
        "description": "local Goose agent for interactive draft/check work",
        "single_instance": True,
    },
    "claude-lab-new": {
        "id": "claude-lab-new",
        "name": "claude: new lab",
        "label": "claude: new lab",
        "tool": "claude",
        "tool_label": "Claude",
        "model": "Claude",
        "launcher": LAB_CLAUDE_LAUNCHER,
        "description": "launch another visible Claude lab agent",
        "single_instance": False,
    },
    "codex-lab-new": {
        "id": "codex-lab-new",
        "name": "codex: new lab",
        "label": "codex: new lab",
        "tool": "codex",
        "tool_label": "Codex",
        "model": "Codex",
        "launcher": LAB_CODEX_LAUNCHER,
        "description": "launch another visible Codex lab agent",
        "single_instance": False,
    },
}


def read_json(path: Path, fallback):
    try:
      return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
      return fallback


def read_events(limit: int) -> list[dict]:
    if not EVENTS_PATH.exists():
        return []
    rows: list[dict] = []
    for line in EVENTS_PATH.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"type": "PARSE_ERROR", "summary": line[:240]})
    return rows[-limit:]


def bounded_int(value: str, *, default: int, lower: int, upper: int) -> int:
    if value == "":
        return default
    parsed = int(value)
    return min(max(parsed, lower), upper)


def task_summary() -> dict:
    graph = read_json(TASK_GRAPH_PATH, {"tasks": []})
    tasks = graph.get("tasks", [])
    counts: dict[str, int] = {}
    for task in tasks:
        status = str(task.get("status", "UNKNOWN"))
        counts[status] = counts.get(status, 0) + 1
    current = [t for t in tasks if t.get("status") in {"READY", "IN_PROGRESS", "SUBMITTED", "CHANGES_REQUESTED"}]
    return {
        "counts": counts,
        "active": current[-12:],
        "total": len(tasks),
    }


def file_url(path: Path) -> str:
    return "file://" + quote(str(path), safe="/:")


def read_project_updater_status() -> dict:
    """Read the manual ProjectUpdater export without touching browser storage."""
    export_payload = None
    export_error = None
    if PROJECT_UPDATER_EXPORT.exists():
        try:
            raw = json.loads(PROJECT_UPDATER_EXPORT.read_text(encoding="utf-8"))
            if raw.get("source") != "ProjectUpdater" or not isinstance(raw.get("stats"), dict):
                raise ValueError("export source/stats fields are not a ProjectUpdater status snapshot")
            if not isinstance(raw.get("projects"), list):
                raise ValueError("export projects field is not a list")
            export_payload = {
                "exportedAt": raw.get("exportedAt"),
                "source": raw.get("source"),
                "stats": raw.get("stats", {}),
                "projects": raw.get("projects", [])[:25],
                "project_count": len(raw.get("projects", [])),
            }
        except Exception as exc:
            export_error = str(exc)
    return {
        "ok": True,
        "project_dir": str(PROJECT_UPDATER_DIR),
        "app_path": str(PROJECT_UPDATER_APP),
        "app_exists": PROJECT_UPDATER_APP.exists(),
        "app_url": file_url(PROJECT_UPDATER_APP),
        "embedded_url": PROJECT_UPDATER_EMBED_PATH,
        "status_export_path": str(PROJECT_UPDATER_EXPORT),
        "status_export_exists": PROJECT_UPDATER_EXPORT.exists(),
        "status_export": export_payload,
        "status_export_error": export_error,
        "data_owner": "ProjectUpdater browser localStorage",
        "command_bridge": {
            "available": PROJECT_UPDATER_APP.exists(),
            "commands": [
                'ai project new "Name" --goal "..." --next-action "..."',
                'ai project update "Name" --progress 50 --status "In progress"',
                'ai project note "Name" "What changed"',
            ],
        },
        "can_read_projects": export_payload is not None,
    }


def open_project_updater() -> tuple[int, dict]:
    """Open the fixed local ProjectUpdater app file through the OS launcher."""
    if not PROJECT_UPDATER_APP.exists():
        return 404, {"ok": False, "error": f"ProjectUpdater app not found at {PROJECT_UPDATER_APP}"}
    try:
        subprocess.Popen(
            ["xdg-open", str(PROJECT_UPDATER_APP)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:
        return 500, {"ok": False, "error": str(exc)}
    return 200, {"ok": True, "opened": str(PROJECT_UPDATER_APP)}


def launch_local_agent(payload: dict) -> tuple[int, dict]:
    agent_id = payload.get("id")
    defs = local_agent_defs()
    if not isinstance(agent_id, str) or agent_id not in defs:
        return 400, {"ok": False, "error": "unknown local agent"}
    item = defs[agent_id]
    launcher = item["launcher"]
    if not launcher.exists():
        return 404, {"ok": False, "error": f"launcher not found: {launcher}"}
    live_names = {
        row.get("base_name") or row.get("name") or ""
        for row in hcom_list_json()
        if row.get("process_bound")
    }
    hcom_name = item.get("hcom_name")
    if item.get("single_instance", True) and hcom_name in live_names:
        return 200, {"ok": True, "already_running": True, "name": item["hcom_name"]}
    env = os.environ.copy()
    env["PROJECT_DIR"] = str(WORKSPACE)
    if hcom_name:
        env["HCOM_NAME"] = hcom_name
    args = [str(launcher), *item.get("launcher_args", [])]
    try:
        subprocess.Popen(
            [str(WEZTERM_BIN), "start", "--cwd", str(WORKSPACE), "--", *args],
            cwd=str(WORKSPACE),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:
        return 500, {"ok": False, "error": str(exc)}
    return 202, {"ok": True, "launched": item["id"], "name": hcom_name}


def project_updater_asset(path: str) -> Path | None:
    """Resolve fixed ProjectUpdater app assets for same-origin embedding."""
    if path in {"/project-updater", "/project-updater/"}:
        return PROJECT_UPDATER_APP
    prefix = "/project-updater/"
    if not path.startswith(prefix):
        return None
    relative = unquote(path[len(prefix):]).lstrip("/")
    if not relative:
        return PROJECT_UPDATER_APP
    candidate = (PROJECT_UPDATER_DIR / "app" / relative).resolve()
    app_root = (PROJECT_UPDATER_DIR / "app").resolve()
    try:
        candidate.relative_to(app_root)
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def run_map_json(argv: list[str], *, cwd: Path, findings_exit_ok: bool = False) -> dict:
    """Run a read-only MAP script and parse its JSON stdout.

    findings_exit_ok: validators exit nonzero when they *find* something while
    still printing their JSON report; treat that as parseable output, not failure.
    """
    try:
        proc = subprocess.run(
            argv,
            cwd=str(cwd),
            text=True,
            capture_output=True,
            timeout=MAP_HEALTH_SCRIPT_TIMEOUT,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"timed out after {MAP_HEALTH_SCRIPT_TIMEOUT}s"}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
    stdout = proc.stdout.strip()
    if proc.returncode != 0 and not (findings_exit_ok and stdout.startswith("{")):
        detail = (proc.stderr or proc.stdout or "").strip()
        return {"ok": False, "error": f"exit {proc.returncode}: {detail[:300]}"}
    try:
        return {"ok": True, "data": json.loads(stdout)}
    except json.JSONDecodeError:
        # Some scripts print log lines before the JSON payload.
        start = stdout.find("{")
        if start >= 0:
            try:
                return {"ok": True, "data": json.loads(stdout[start:])}
            except json.JSONDecodeError:
                pass
        return {"ok": False, "error": f"non-JSON output: {stdout[:200]}"}


def map_python() -> str:
    return str(MAP_VENV_PY) if MAP_VENV_PY.exists() else sys.executable


def runner_health() -> dict:
    result = run_map_json([map_python(), str(MAP_DIR / "graph" / "runner.py")], cwd=WORKSPACE)
    if not result["ok"]:
        return {"status": "error", "text": result["error"]}
    data = result["data"]
    halt = (data.get("halt_state") or {}).get("state", "unknown")
    ready = len(data.get("ready_tasks") or [])
    in_progress = len(data.get("in_progress_tasks") or [])
    submitted = len(data.get("submitted_tasks") or [])
    blocked = len(data.get("blocked_tasks") or []) + len(data.get("dispatch_blocked_tasks") or [])
    status = "ok"
    if halt != "clear":
        status = "warn"
    if blocked:
        status = "warn"
    return {
        "status": status,
        "text": f"route {data.get('next_route', '?')} · {ready} ready · {in_progress} in-progress · {submitted} submitted",
        "route": data.get("next_route"),
        "halt": halt,
        "ready": ready,
        "in_progress": in_progress,
        "submitted": submitted,
        "blocked": blocked,
    }


def librarian_health() -> dict:
    result = run_map_json(
        ["python3", str(MAP_DIR / "scripts" / "librarian.py"), "validate"],
        cwd=MAP_DIR,
        findings_exit_ok=True,
    )
    if not result["ok"]:
        return {"status": "error", "text": result["error"]}
    count = int(result["data"].get("finding_count", 0))
    return {
        "status": "ok" if count == 0 else "warn",
        "text": "wikilinks resolve" if count == 0 else f"{count} broken/ambiguous wikilinks",
        "finding_count": count,
    }


def replay_health() -> dict:
    result = run_map_json(
        ["python3", str(MAP_DIR / "scripts" / "session_replay.py"), "status"],
        cwd=WORKSPACE,
    )
    if not result["ok"]:
        return {"status": "error", "text": result["error"]}
    data = result["data"]
    drift = len(data.get("drift_findings") or [])
    safe = bool(data.get("safe_for_mission_control"))
    rows = (data.get("row_counts") or {}).get("map_events_jsonl", 0)
    exists = bool(data.get("exists"))
    if not exists:
        return {"status": "warn", "text": "replay index not built", "exists": False}
    status = "ok" if safe and drift == 0 else "warn"
    text = f"{rows} events indexed" + ("" if drift == 0 else f" · {drift} drift findings")
    if not safe:
        text += " · unsafe for mission-control"
    return {"status": status, "text": text, "safe": safe, "drift_findings": drift, "rows": rows}


def watcher_process_health() -> dict:
    if not WATCHER_PIDFILE.exists():
        return {"status": "warn", "text": "watcher pidfile missing", "running": False}
    try:
        raw_pid = WATCHER_PIDFILE.read_text(encoding="utf-8").strip()
        pid = int(raw_pid)
    except (OSError, ValueError) as exc:
        return {"status": "error", "text": f"watcher pidfile unreadable: {exc}", "running": False}
    cmdline = Path("/proc") / str(pid) / "cmdline"
    try:
        text = cmdline.read_bytes().replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError:
        return {"status": "error", "text": f"watcher pidfile stale (pid {pid} not running)", "running": False, "pid": pid}
    if "limit_watcher.py" not in text:
        return {"status": "error", "text": f"pid {pid} is not limit_watcher.py", "running": False, "pid": pid}
    return {"status": "ok", "text": f"watcher running pid {pid}", "running": True, "pid": pid}


def rns_health() -> dict:
    process = watcher_process_health()
    if not WATCHER_STATE_PATH.exists():
        status = "error" if process.get("status") == "error" else "warn"
        return {**process, "status": status, "text": f"{process.get('text')} · no watcher state file"}
    state = read_json(WATCHER_STATE_PATH, None)
    if not isinstance(state, dict):
        return {**process, "status": "error", "text": f"{process.get('text')} · watcher state unreadable"}
    incidents = state.get("incidents") or {}
    open_incidents = [
        name for name, entry in incidents.items()
        if isinstance(entry, dict) and not entry.get("reset_at")
    ]
    gave_up = [
        name for name in open_incidents
        if incidents[name].get("gave_up")
    ]
    live = state.get("last_live") or []
    status = "ok" if not open_incidents else "warn"
    if process.get("status") == "error":
        status = "error"
    elif process.get("status") == "warn" and status == "ok":
        status = "warn"
    if open_incidents:
        text = f"{process.get('text')} · {len(open_incidents)} open incidents ({len(gave_up)} gave-up) · {len(live)} last-live"
    else:
        text = f"{process.get('text')} · no open incidents · {len(live)} last-live"
    return {
        "status": status,
        "text": text,
        "running": process.get("running"),
        "pid": process.get("pid"),
        "open_incidents": len(open_incidents),
        "gave_up": gave_up,
        "last_live": live,
    }


def token_health(*, force: bool = False) -> dict:
    result = token_status_snapshot(force=force)
    if not result["ok"]:
        return {"status": "error", "text": result["error"]}
    data = result["data"]
    totals = data.get("totals") or {}
    agents = data.get("agents") or []
    unattached = data.get("unattached_recent_claude_transcripts") or []
    codex_percent = None
    codex_reset = None
    missing = 0
    limits = 0
    for agent in agents:
        if not agent.get("transcript_found"):
            missing += 1
        metrics = agent.get("metrics") or {}
        if agent.get("tool") == "codex" and metrics.get("primary_used_percent") is not None:
            codex_percent = metrics.get("primary_used_percent")
            codex_reset = metrics.get("primary_resets_at")
        if metrics.get("limit"):
            limits += 1
    limits += sum(1 for item in unattached if (item.get("metrics") or {}).get("limit"))
    status = "ok"
    if missing or limits:
        status = "warn"
    claude_non_cached = int(totals.get("claude_non_cached_tokens") or 0)
    unattached_total = int(totals.get("claude_unattached_recent_total_tokens") or 0)
    codex_text = f"Codex {codex_percent:g}% used" if isinstance(codex_percent, (int, float)) else "Codex percent unavailable"
    text = f"{codex_text} · Claude non-cached {claude_non_cached:,}"
    if unattached_total:
        text += f" · {unattached_total:,} unattached observed"
    if missing:
        text += f" · {missing} missing transcript"
    if limits:
        text += f" · {limits} limit note"
    return {
        "status": status,
        "text": text,
        "codex_primary_used_percent": codex_percent,
        "codex_primary_resets_at": codex_reset,
        "claude_non_cached_tokens": claude_non_cached,
        "claude_total_tokens": int(totals.get("claude_total_tokens") or 0),
        "missing_transcripts": missing,
        "limit_notes": limits,
        "unattached_recent_count": len(unattached),
    }


def cost_yield_health() -> dict:
    """TASK-200-series: productive/pending/abandoned proxy-spend split, from
    cost_yield.py (read-only, mode=ro DB). Surfaced so the release-gate-
    backlog finding (operator report, TASK-190) is glanceable, not buried."""
    result = run_map_json(
        [map_python(), str(MAP_DIR / "scripts" / "cost_yield.py"), "--json"],
        cwd=MAP_DIR,
    )
    if not result["ok"]:
        return {"status": "error", "text": result["error"]}
    split = (result["data"] or {}).get("spend_split") or {}
    productive = (split.get("productive") or {}).get("event_percent", 0.0)
    pending = split.get("pending") or {}
    pending_percent = pending.get("event_percent", 0.0)
    pending_tasks = pending.get("tasks", 0)
    abandoned_percent = (split.get("abandoned") or {}).get("event_percent", 0.0)
    status = "warn" if pending_percent >= 30 else "ok"
    text = (
        f"{productive:g}% shipped · {pending_percent:g}% parked ({pending_tasks}) "
        f"· {abandoned_percent:g}% abandoned"
    )
    return {
        "status": status,
        "text": text,
        "productive_percent": productive,
        "pending_percent": pending_percent,
        "pending_tasks": pending_tasks,
        "abandoned_percent": abandoned_percent,
    }


def outcomes_health() -> dict:
    """TASK-200-series: outcome-feedback validator blind-spot rate, from
    map_metrics.py's outcome_feedback block (TASK-189)."""
    result = run_map_json(
        [map_python(), str(MAP_DIR / "scripts" / "map_metrics.py"), "--json"],
        cwd=MAP_DIR,
    )
    if not result["ok"]:
        return {"status": "error", "text": result["error"]}
    feedback = (result["data"] or {}).get("outcome_feedback") or {}
    count = int(feedback.get("outcome_event_count") or 0)
    blind_count = int(feedback.get("validator_blind_spot_count") or 0)
    blind_denominator = int(feedback.get("validator_blind_spot_denominator") or 0)
    rate = feedback.get("validator_blind_spot_rate")
    if count == 0:
        return {
            "status": "warn",
            "text": "no outcomes recorded yet",
            "outcome_event_count": 0,
            "blind_spot_count": 0,
            "blind_spot_denominator": 0,
        }
    status = "warn" if blind_count else "ok"
    text = f"{count} outcomes · blind-spot {blind_count}/{blind_denominator}"
    return {
        "status": status,
        "text": text,
        "outcome_event_count": count,
        "blind_spot_count": blind_count,
        "blind_spot_denominator": blind_denominator,
        "blind_spot_rate": rate,
    }


_MAP_HEALTH_LOCK = threading.Lock()
_MAP_HEALTH_CACHE: dict = {"at": 0.0, "payload": None}
_TOKEN_STATUS_LOCK = threading.Lock()
_TOKEN_STATUS_CACHE: dict = {"at": 0.0, "payload": None}

_HEALTH_SOURCES = {
    "runner": runner_health,
    "librarian": librarian_health,
    "replay": replay_health,
    "rns": rns_health,
    "tokens": token_health,
    "cost_yield": cost_yield_health,
    "outcomes": outcomes_health,
}

_STATUS_RANK = {"ok": 0, "warn": 1, "error": 2}


def token_status_snapshot(*, force: bool = False) -> dict:
    """Read token status with a short cache for presence and health polling."""
    with _TOKEN_STATUS_LOCK:
        cached = _TOKEN_STATUS_CACHE["payload"]
        if not force and cached is not None and time.monotonic() - _TOKEN_STATUS_CACHE["at"] < MAP_HEALTH_TTL_SECONDS:
            return cached
        result = run_map_json(
            ["python3", str(MAP_DIR / "scripts" / "agent_token_status.py"), "--json"],
            cwd=WORKSPACE,
        )
        _TOKEN_STATUS_CACHE["payload"] = result
        _TOKEN_STATUS_CACHE["at"] = time.monotonic()
        return result


def map_health(*, force: bool = False) -> dict:
    """Aggregate read-only MAP runtime health, cached briefly for UI polling."""
    with _MAP_HEALTH_LOCK:
        cached = _MAP_HEALTH_CACHE["payload"]
        if not force and cached is not None and time.monotonic() - _MAP_HEALTH_CACHE["at"] < MAP_HEALTH_TTL_SECONDS:
            return cached
        with ThreadPoolExecutor(max_workers=len(_HEALTH_SOURCES)) as pool:
            futures = {
                name: pool.submit(token_health, force=force) if name == "tokens" else pool.submit(fn)
                for name, fn in _HEALTH_SOURCES.items()
            }
            sources: dict[str, dict] = {}
            for name, future in futures.items():
                try:
                    sources[name] = future.result()
                except Exception as exc:
                    sources[name] = {"status": "error", "text": str(exc)}
        overall = max(
            (source.get("status", "error") for source in sources.values()),
            key=lambda status: _STATUS_RANK.get(status, 2),
        )
        payload = {
            "ok": True,
            "overall": overall,
            "sources": sources,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "ttl_seconds": MAP_HEALTH_TTL_SECONDS,
        }
        _MAP_HEALTH_CACHE["payload"] = payload
        _MAP_HEALTH_CACHE["at"] = time.monotonic()
        return payload


def hcom_connect():
    import sqlite3

    # mode=ro so the UI can never write hcom state, even by accident.
    return sqlite3.connect(f"file:{HCOM_DB}?mode=ro", uri=True, timeout=2)


def hcom_list_json() -> list[dict]:
    """Return live hcom instances, preferring hcom's process-bound view."""
    try:
        proc = subprocess.run(
            ["hcom", "list", "--json"],
            cwd=str(WORKSPACE),
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return []
    if proc.returncode != 0:
        return []
    stdout = proc.stdout.strip()
    try:
        data = json.loads(stdout)
    except json.JSONDecodeError:
        start = stdout.find("[")
        if start < 0:
            return []
        try:
            data = json.loads(stdout[start:])
        except json.JSONDecodeError:
            return []
    return data if isinstance(data, list) else []


def local_agent_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48] or "model"


def ollama_models() -> list[dict]:
    try:
        proc = subprocess.run(
            ["ollama", "list"],
            cwd=str(WORKSPACE),
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
    except Exception:
        return []
    if proc.returncode != 0:
        return []
    rows = []
    for line in proc.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 3:
            continue
        name = parts[0]
        size = " ".join(parts[2:4]) if len(parts) >= 4 else parts[2]
        rows.append({"name": name, "size": size})
    return rows


def local_agent_defs() -> dict[str, dict]:
    defs = {key: dict(value) for key, value in BASE_LOCAL_AGENT_DEFS.items()}
    for model in ollama_models():
        model_name = model["name"]
        slug = local_agent_slug(model_name)
        agent_id = f"ollama-model-{slug}"
        defs[agent_id] = {
            "id": agent_id,
            "name": f"ollama: {model_name}",
            "label": f"ollama: {model_name}",
            "tool": "ollama",
            "tool_label": "Ollama",
            "model": model_name,
            "hcom_name": f"ollama-{slug}",
            "launcher": OLLAMA_MODEL_LAUNCHER,
            "launcher_args": [model_name, f"ollama-{slug}"],
            "description": OLLAMA_MODEL_USES.get(model_name, "local draft, check, and summary support"),
            "size": model.get("size", ""),
            "single_instance": True,
        }
    return defs


def read_chat(since_id: int, limit: int) -> dict:
    if not HCOM_DB.exists():
        return {"ok": False, "error": f"hcom database not found at {HCOM_DB}", "messages": []}
    try:
        con = hcom_connect()
        try:
            if since_id > 0:
                rows = con.execute(
                    "SELECT id, timestamp, data FROM events"
                    " WHERE type='message' AND id > ? ORDER BY id ASC LIMIT ?",
                    (since_id, limit),
                ).fetchall()
            else:
                rows = con.execute(
                    "SELECT id, timestamp, data FROM events"
                    " WHERE type='message' ORDER BY id DESC LIMIT ?",
                    (limit,),
                ).fetchall()
                rows.reverse()
        finally:
            con.close()
    except Exception as exc:
        return {"ok": False, "error": str(exc), "messages": []}
    messages = []
    for event_id, timestamp, data in rows:
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            continue
        message = {
            "id": event_id,
            "ts": timestamp,
            "sender": payload.get("from", "?"),
            "sender_kind": payload.get("sender_kind", ""),
            "intent": payload.get("intent", ""),
            "mentions": payload.get("mentions", []),
            "reply_to": payload.get("reply_to"),
            "scope": payload.get("scope", ""),
            "text": payload.get("text", ""),
        }
        message["summary"] = SUMMARIZER.get(event_id)
        if message["summary"] is None and Summarizer.eligible(message):
            SUMMARIZER.enqueue(message)
        messages.append(message)
    attach_quotes(messages)
    return {"ok": True, "messages": messages, "operator": OPERATOR_NAME}


def attach_quotes(messages: list[dict]) -> None:
    """Batch-fetch the messages these replies point at, as quote context."""
    reply_ids = []
    for msg in messages:
        raw = str(msg.get("reply_to") or "").split(":")[0]
        if raw.isdigit():
            reply_ids.append(int(raw))
    if not reply_ids:
        return
    quotes = {}
    try:
        con = hcom_connect()
        try:
            rows = con.execute(
                "SELECT id, data FROM events WHERE type='message' AND id IN (%s)"
                % ",".join("?" * len(set(reply_ids))),
                tuple(set(reply_ids)),
            ).fetchall()
        finally:
            con.close()
        for event_id, data in rows:
            payload = json.loads(data)
            quotes[event_id] = {
                "id": event_id,
                "sender": payload.get("from", "?"),
                "text": payload.get("text", "")[:200],
            }
    except Exception:
        return
    for msg in messages:
        raw = str(msg.get("reply_to") or "").split(":")[0]
        if raw.isdigit():
            msg["quote"] = quotes.get(int(raw))


def read_attention() -> dict:
    """Unanswered intent=request messages addressed to the operator."""
    try:
        con = hcom_connect()
        try:
            rows = con.execute(
                "SELECT id, timestamp, data FROM events"
                " WHERE type='message' ORDER BY id DESC LIMIT 600",
            ).fetchall()
        finally:
            con.close()
    except Exception as exc:
        return {"ok": False, "error": str(exc), "items": []}
    operator_names = {OPERATOR_NAME, "bigboss"}
    # Only requests from agents still in the room are answerable; questions
    # from dead sessions would otherwise pile up here forever.
    live_senders = {a["name"] for a in read_presence().get("agents", [])}
    answered: set[int] = set()
    items = []
    for event_id, timestamp, data in rows:  # newest first
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            continue
        raw_reply = str(payload.get("reply_to") or "").split(":")[0]
        if raw_reply.isdigit():
            answered.add(int(raw_reply))
        if payload.get("intent") != "request":
            continue
        if payload.get("sender_kind") != "instance":
            continue
        if not operator_names & set(payload.get("mentions", [])):
            continue
        if event_id in answered:
            continue
        if payload.get("from") not in live_senders:
            continue
        items.append({
            "id": event_id,
            "ts": timestamp,
            "sender": payload.get("from", "?"),
            "text": payload.get("text", "")[:500],
            "summary": SUMMARIZER.get(event_id),
        })
    items.reverse()  # oldest first
    return {"ok": True, "items": items}


def agent_tool(name: str, tag: str, token_row: dict | None) -> str:
    raw = (token_row or {}).get("tool")
    if isinstance(raw, str) and raw:
        return raw
    marker = f"{name} {tag}".lower()
    if "claude" in marker:
        return "claude"
    if "codex" in marker:
        return "codex"
    if "gemini" in marker:
        return "gemini"
    if "opencode" in marker:
        return "opencode"
    if "ollama" in marker or "goose" in marker:
        return "ollama"
    return "unknown"


def tool_label(tool: str) -> str:
    return {
        "claude": "Claude",
        "codex": "Codex",
        "gemini": "Gemini",
        "opencode": "OpenCode",
        "ollama": "Ollama",
    }.get(tool, "Other")


def _usage_status(used_percent: float) -> str:
    if used_percent >= 90:
        return "error"
    if used_percent >= 70:
        return "warn"
    return "ok"


def _format_percent(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def limit_reset_label(limit: dict | None) -> str:
    if not limit:
        return "reset noted"
    reset_at = limit.get("reset_at")
    if isinstance(reset_at, str) and reset_at:
        try:
            when = datetime.fromisoformat(reset_at)
            return "resets " + when.strftime("%-I:%M %p")
        except Exception:
            pass
    text = str(limit.get("text") or "")
    match = re.search(r"resets\s+([^()]+)", text, re.IGNORECASE)
    if match:
        return "resets " + match.group(1).strip()
    return "reset noted"


def parse_iso_datetime(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def replace_rns_sync_note(notes: object, sync_note: str | None) -> str:
    existing = str(notes or "")
    parts = [part.strip() for part in existing.split(" | ") if part.strip() and RNS_SYNC_NOTE_MARKER not in part]
    if sync_note:
        parts.append(sync_note)
    return " | ".join(parts)


def agent_usage_summary(tool: str, token_row: dict | None) -> dict:
    if not token_row:
        return {
            "kind": "unknown",
            "status": "unknown",
            "label": "no token link",
            "remaining_label": "unknown",
            "used_percent": None,
        }
    if not token_row.get("transcript_found"):
        return {
            "kind": "missing",
            "status": "warn",
            "label": "no transcript",
            "remaining_label": "unknown",
            "used_percent": None,
            "transcript_path": token_row.get("transcript_path"),
        }
    metrics = token_row.get("metrics") or {}
    if not metrics.get("available"):
        return {
            "kind": "empty",
            "status": "unknown",
            "label": "no token records",
            "remaining_label": "unknown",
            "used_percent": None,
        }
    if tool == "codex":
        used = metrics.get("primary_used_percent")
        if isinstance(used, (int, float)):
            used_float = max(0.0, min(100.0, float(used)))
            remaining = max(0.0, 100.0 - used_float)
            return {
                "kind": "rate_limit_percent",
                "status": _usage_status(used_float),
                "label": f"{_format_percent(used_float)}% used",
                "remaining_label": f"{_format_percent(remaining)}% left",
                "used_percent": used_float,
                "total_tokens": metrics.get("total_tokens"),
                "last_tokens": metrics.get("last_tokens"),
                "context_window": metrics.get("context_window"),
                "resets_at": metrics.get("primary_resets_at"),
            }
        return {
            "kind": "observed",
            "status": "unknown",
            "label": "percent unavailable",
            "remaining_label": "unknown",
            "used_percent": None,
            "total_tokens": metrics.get("total_tokens"),
        }
    if tool == "claude":
        limit = metrics.get("limit")
        if limit:
            return {
                "kind": "limit",
                "status": "error",
                "label": "limit note",
                "remaining_label": limit_reset_label(limit),
                "used_percent": 100.0,
                "total_tokens": metrics.get("total_tokens"),
                "non_cached_tokens": metrics.get("non_cached_tokens"),
                "limit_text": limit.get("text"),
                "limit_timestamp": limit.get("timestamp"),
                "reset_at": limit.get("reset_at"),
            }
        return {
            "kind": "observed",
            "status": "unknown",
            "label": "observed usage",
            "remaining_label": "no % exposed",
            "used_percent": None,
            "total_tokens": metrics.get("total_tokens"),
            "non_cached_tokens": metrics.get("non_cached_tokens"),
            "turns": metrics.get("turns"),
        }
    return {
        "kind": "unknown",
        "status": "unknown",
        "label": "usage unknown",
        "remaining_label": "unknown",
        "used_percent": None,
    }


def local_agent_shortcuts(live_names: set[str]) -> list[dict]:
    shortcuts = []
    for item in local_agent_defs().values():
        hcom_name = item.get("hcom_name")
        if item.get("single_instance", True) and hcom_name in live_names:
            continue
        shortcuts.append({
            "id": item["id"],
            "name": item["name"],
            "tag": "local",
            "tool": item["tool"],
            "tool_label": item["tool_label"],
            "model": item["model"],
            "status": "available",
            "age_seconds": None,
            "context": "launch on demand",
            "process_bound": False,
            "shortcut": True,
            "launchable": item["launcher"].exists(),
            "description": item.get("description", ""),
            "size": item.get("size", ""),
            "usage": local_agent_usage(item, running=False),
        })
    return shortcuts


def local_agent_usage(item: dict, *, running: bool) -> dict:
    return {
        "kind": "local",
        "status": "unknown",
        "label": item.get("description") or "local helper",
        "remaining_label": "running" if running else (item.get("size") or "on demand"),
        "used_percent": None,
    }


def provider_usage_summary(token_data: dict) -> dict[str, dict]:
    agents = token_data.get("agents") or []
    unattached = token_data.get("unattached_recent_claude_transcripts") or []
    totals = token_data.get("totals") or {}
    provider_usage: dict[str, dict] = {}

    codex_usages = []
    for row in agents:
        if row.get("tool") != "codex":
            continue
        usage = agent_usage_summary("codex", row)
        if isinstance(usage.get("used_percent"), (int, float)):
            codex_usages.append(usage)
    if codex_usages:
        provider_usage["codex"] = max(codex_usages, key=lambda usage: usage.get("used_percent") or 0)

    claude_limit_count = 0
    latest_limit = None
    for row in agents:
        if row.get("tool") == "claude":
            limit = (row.get("metrics") or {}).get("limit")
            if limit:
                claude_limit_count += 1
                latest_limit = limit
    for item in unattached:
        limit = (item.get("metrics") or {}).get("limit")
        if limit:
            claude_limit_count += 1
            latest_limit = limit
    claude_non_cached = int(totals.get("claude_non_cached_tokens") or 0)
    claude_total = int(totals.get("claude_total_tokens") or 0)
    if claude_limit_count:
        provider_usage["claude"] = {
            "kind": "limit",
            "status": "error",
            "label": f"{claude_limit_count} limit note{'' if claude_limit_count == 1 else 's'}",
            "remaining_label": limit_reset_label(latest_limit),
            "used_percent": 100.0,
            "total_tokens": claude_total,
            "non_cached_tokens": claude_non_cached,
            "limit_text": (latest_limit or {}).get("text"),
            "limit_timestamp": (latest_limit or {}).get("timestamp"),
            "reset_at": (latest_limit or {}).get("reset_at"),
        }
    elif claude_non_cached or claude_total:
        provider_usage["claude"] = {
            "kind": "observed",
            "status": "unknown",
            "label": f"{claude_non_cached:,} non-cached" if claude_non_cached else "observed usage",
            "remaining_label": "no % exposed",
            "used_percent": None,
            "total_tokens": claude_total,
            "non_cached_tokens": claude_non_cached,
            "unattached_recent_count": len(unattached),
        }
    return provider_usage


def sync_rns_provider_limits(provider_usage: dict[str, dict]) -> dict:
    """Publish provider-limit reset times into the RnS status board.

    RnS watches agents/status.json for standby/out_of_tokens + ISO resume_after.
    Claude exposes limits at the provider/session-pool level, so when a Claude
    provider limit is active we mark live Claude lab agents with the same reset
    window. Entries previously marked by this sync are cleared when the provider
    limit is no longer active.
    """
    board = read_json(AGENTS_STATUS_PATH, {"agents": {}})
    agents = board.setdefault("agents", {})
    if not isinstance(agents, dict):
        return {"ok": False, "error": "agents/status.json has no agents object"}

    now = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    changed = False
    marked: list[str] = []
    cleared: list[str] = []
    claude_usage = provider_usage.get("claude") or {}
    reset_at = claude_usage.get("reset_at") if claude_usage.get("kind") == "limit" else None
    reset_dt = parse_iso_datetime(reset_at)
    live_claude = sorted(
        row.get("name")
        for row in hcom_list_json()
        if row.get("tool") == "claude" and row.get("process_bound") and row.get("name")
    )

    if reset_dt and live_claude:
        sync_note = (
            f"[{RNS_SYNC_NOTE_MARKER}] Claude provider limit; "
            f"{claude_usage.get('remaining_label') or 'reset scheduled'}; synced {now}"
        )
        for name in live_claude:
            entry = agents.setdefault(name, {})
            before = json.dumps(entry, sort_keys=True)
            entry["status"] = "standby"
            entry["reason"] = "out_of_tokens"
            entry["resume_after"] = reset_dt.isoformat()
            entry["notes"] = replace_rns_sync_note(entry.get("notes"), sync_note)
            if json.dumps(entry, sort_keys=True) != before:
                changed = True
            marked.append(name)
    else:
        for name, entry in agents.items():
            if not isinstance(entry, dict):
                continue
            notes = str(entry.get("notes") or "")
            if RNS_SYNC_NOTE_MARKER not in notes:
                continue
            before = json.dumps(entry, sort_keys=True)
            entry["notes"] = replace_rns_sync_note(notes, None)
            if entry.get("reason") == "out_of_tokens":
                entry["status"] = "available"
                entry["reason"] = None
                entry["resume_after"] = None
            if json.dumps(entry, sort_keys=True) != before:
                changed = True
                cleared.append(name)

    if changed:
        tmp = AGENTS_STATUS_PATH.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(board, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(AGENTS_STATUS_PATH)
    return {
        "ok": True,
        "changed": changed,
        "marked": marked,
        "cleared": cleared,
        "reset_at": reset_dt.isoformat() if reset_dt else None,
    }


def read_presence(*, force_usage: bool = False) -> dict:
    hcom_agents = hcom_list_json()
    db_rows = []
    if not hcom_agents and not HCOM_DB.exists():
        return {"ok": False, "error": f"hcom database not found at {HCOM_DB}", "agents": []}
    if not hcom_agents:
        try:
            con = hcom_connect()
            try:
                db_rows = con.execute(
                    "SELECT name, tag, status, status_time, status_context FROM instances"
                    " ORDER BY status_time DESC",
                ).fetchall()
            finally:
                con.close()
        except Exception as exc:
            return {"ok": False, "error": str(exc), "agents": []}
    now = time.time()
    agents = []
    token_rows: dict[str, dict] = {}
    token_data: dict = {}
    token_result = token_status_snapshot(force=force_usage)
    if token_result.get("ok"):
        token_data = token_result.get("data") or {}
        for row in token_data.get("agents") or []:
            name = row.get("name")
            if isinstance(name, str) and name:
                token_rows[name] = row
                for prefix in ("claude-lab-", "codex-lab-", "gemini-lab-", "opencode-lab-"):
                    if name.startswith(prefix):
                        token_rows[name.removeprefix(prefix)] = row
                        break
    if hcom_agents:
        rows = [
            (
                row.get("base_name") or row.get("name") or "",
                row.get("tag") or "",
                row.get("status") or "unknown",
                row.get("status_age_seconds"),
                row.get("status_context") or "",
                row.get("process_bound"),
            )
            for row in hcom_agents
            if row.get("process_bound") or row.get("status") in {"active", "listening", "blocked"}
        ]
    else:
        rows = []
        for name, tag, status, status_time, context in db_rows:
            age = max(0, int(now - status_time)) if status_time else None
            # Sessions silent for over an hour are gone, not idle; hide them so
            # the sidebar shows the actual room. Only apply this fallback when
            # hcom list --json is unavailable; hcom process_bound is stronger.
            if age is not None and age > 3600 and status != "active":
                continue
            rows.append((name, tag or "", status or "unknown", age, context or "", None))
    local_by_hcom = {
        item["hcom_name"]: item
        for item in local_agent_defs().values()
        if item.get("hcom_name")
    }
    live_names = set()
    for name, tag, status, age, context, process_bound in rows:
        live_names.add(name)
        token_row = token_rows.get(name)
        local_def = local_by_hcom.get(name)
        tool = local_def.get("tool") if local_def else agent_tool(name, tag or "", token_row)
        metrics = (token_row or {}).get("metrics") or {}
        agents.append({
            "name": name,
            "tag": tag or "",
            "tool": tool,
            "tool_label": local_def.get("tool_label") if local_def else tool_label(tool),
            "model": local_def.get("model") if local_def else metrics.get("model_label") or metrics.get("model") or tool_label(tool),
            "status": status or "unknown",
            "age_seconds": age,
            "context": context or local_def.get("description", "") if local_def else context or "",
            "process_bound": process_bound,
            "usage": local_agent_usage(local_def, running=True) if local_def else agent_usage_summary(tool, token_row),
        })
    return {
        "ok": True,
        "agents": agents,
        "shortcuts": local_agent_shortcuts(live_names),
        "provider_usage": provider_usage_summary(token_data),
        "operator": OPERATOR_NAME,
    }


def send_chat(payload: dict) -> tuple[int, dict]:
    """Operator chat send: @mentions parsed from the text, else broadcast."""
    text = payload.get("text")
    if not isinstance(text, str) or not text.strip():
        return 400, {"ok": False, "error": "text is required"}
    if len(text) > 4000:
        return 400, {"ok": False, "error": "message is too long (4000 chars max)"}
    text = text.strip()

    mentions = [f"@{name}" for name in MENTION_RE.findall(text)]
    cmd = ["hcom", "send", *mentions, "--intent", "inform", "--from", OPERATOR_NAME]
    reply_to = payload.get("reply_to")
    if reply_to:
        if not str(reply_to).replace(":", "").isalnum():
            return 400, {"ok": False, "error": "reply_to must be an hcom id"}
        cmd.extend(["--reply-to", str(reply_to)])
    cmd.extend(["--", text])

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(WORKSPACE),
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except Exception as exc:
        return 500, {"ok": False, "error": str(exc)}
    ok = proc.returncode == 0
    return (200 if ok else 502), {
        "ok": ok,
        "sent_as": OPERATOR_NAME,
        "mentions": mentions,
        "broadcast": not mentions,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


class Summarizer:
    """Plain-English gists of agent messages via the local Ollama model.

    Local-model policy (notes/local-model-helper-guide.md): summaries are
    scoped support output, never authority — the UI always keeps the verbatim
    message one click away. Runs in a single background thread; chat delivery
    never waits on it. Cache is per hcom event id, persisted across restarts.
    """

    def __init__(self):
        import queue
        import threading

        self.lock = threading.Lock()
        self.queue = queue.Queue()
        self.queued: set[int] = set()
        self.failed: dict[int, int] = {}
        try:
            self.cache: dict[str, str] = json.loads(SUMMARY_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            self.cache = {}
        self.available: bool | None = None  # unknown until first attempt
        threading.Thread(target=self._worker, daemon=True).start()

    @staticmethod
    def eligible(msg: dict) -> bool:
        # Agents only: operator, system, launcher, and any other external
        # sender_kind must never be paraphrased (review finding, TASK-092).
        if msg.get("sender_kind") != "instance":
            return False
        if msg.get("sender") in {OPERATOR_NAME, "[hcom-events]"}:
            return False
        text = msg.get("text", "")
        stripped = text.strip()
        return len(stripped) >= 40 or stripped.startswith("!")

    def get(self, event_id: int) -> str | None:
        return self.cache.get(str(event_id))

    def enqueue(self, msg: dict) -> None:
        event_id = msg["id"]
        with self.lock:
            if (str(event_id) in self.cache or event_id in self.queued
                    or self.failed.get(event_id, 0) >= 2):
                return
            self.queued.add(event_id)
        self.queue.put(msg)

    def recent(self, since_id: int) -> dict[str, str]:
        with self.lock:
            return {k: v for k, v in self.cache.items() if int(k) > since_id}

    @staticmethod
    def clean_response(summary: str) -> str:
        summary = summary.replace("\r\n", "\n").replace("\r", "\n").strip()
        summary = re.sub(r"(?is)```(?:\w+)?\s*(.*?)\s*```", r"\1", summary).strip()
        if re.match(r"(?i)^here(?:'s| is)\b", summary):
            quoted = re.findall(r'"([^"]+)"|“([^”]+)”', summary)
            if quoted:
                summary = next((a or b for a, b in reversed(quoted) if a or b), summary)
            else:
                summary = re.sub(r"(?i)^here(?:'s| is)\b.*?:\s*", "", summary).strip()
        summary = re.sub(r"(?i)^(relay|rewritten|casual relay)\s*:\s*", "", summary).strip()
        lines = []
        for line in summary.splitlines():
            cleaned = " ".join(line.split()).strip()
            if not cleaned:
                continue
            cleaned = cleaned.strip('"“”').strip()
            if cleaned:
                lines.append(cleaned)
        return "\n".join(lines[:6]).strip()

    def _worker(self) -> None:
        import urllib.request

        while True:
            msg = self.queue.get()
            event_id = msg["id"]
            try:
                body = json.dumps({
                    "model": SUMMARY_MODEL,
                    "stream": False,
                    "keep_alive": "30m",
                    "options": {"temperature": 0.1, "num_predict": 180},
                    "prompt": SUMMARY_PROMPT.format(
                        sender=msg.get("sender", "an agent"), text=msg.get("text", "")[:2000]),
                }).encode("utf-8")
                request = urllib.request.Request(
                    f"{OLLAMA_URL}/api/generate", data=body,
                    headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(request, timeout=120) as response:
                    summary = json.load(response).get("response", "").strip()
                summary = self.clean_response(summary)[:900]
                if not summary:
                    raise ValueError("empty summary")
                with self.lock:
                    self.available = True
                    self.cache[str(event_id)] = summary
                    self.queued.discard(event_id)
                    try:
                        SUMMARY_CACHE_PATH.parent.mkdir(exist_ok=True)
                        SUMMARY_CACHE_PATH.write_text(
                            json.dumps(self.cache, indent=0), encoding="utf-8")
                    except Exception:
                        pass
            except Exception:
                with self.lock:
                    if self.available is None:
                        self.available = False
                    self.failed[event_id] = self.failed.get(event_id, 0) + 1
                    self.queued.discard(event_id)


SUMMARIZER = Summarizer()


def lab_agents_present() -> list[str]:
    hcom_agents = hcom_list_json()
    if hcom_agents:
        return [
            row.get("base_name") or row.get("name") or ""
            for row in hcom_agents
            if row.get("tag") in LAB_TAGS
            and row.get("status") in {"active", "listening", "blocked"}
            and row.get("process_bound")
        ]
    try:
        con = hcom_connect()
        try:
            rows = con.execute(
                "SELECT name, tag, status, status_time FROM instances WHERE tag IN (%s)"
                % ",".join("?" * len(LAB_TAGS)),
                tuple(sorted(LAB_TAGS)),
            ).fetchall()
        finally:
            con.close()
    except Exception:
        return []
    now = time.time()
    return [
        name for name, _tag, status, status_time in rows
        if status in {"active", "listening", "blocked"}
        and status_time and now - status_time < 3600
    ]


def watcher_running() -> bool:
    try:
        pid = int(WATCHER_PIDFILE.read_text().strip())
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def lab_status() -> dict:
    return {
        "ok": True,
        "agents": lab_agents_present(),
        "watcher": watcher_running(),
        "launcher": str(LAB_LAUNCHER),
        "launcher_available": LAB_LAUNCHER.exists(),
    }


def start_lab() -> tuple[int, dict]:
    if not LAB_LAUNCHER.exists():
        return 501, {"ok": False, "error": f"lab launcher not found at {LAB_LAUNCHER}"}
    agents = lab_agents_present()
    if agents:
        # Agents alive but watcher down: revive just the watcher instead of
        # opening a second wezterm lab.
        if not watcher_running():
            watcher_script = MAP_DIR / "scripts" / "start-limit-watcher.sh"
            try:
                subprocess.run([str(watcher_script), "60"], cwd=str(WORKSPACE),
                               capture_output=True, timeout=15, check=False)
            except Exception:
                pass
        return 200, {"ok": True, "already_running": True, "agents": agents,
                     "watcher": watcher_running()}
    try:
        subprocess.Popen(
            [str(LAB_LAUNCHER)],
            cwd=str(WORKSPACE),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as exc:
        return 500, {"ok": False, "error": str(exc)}
    return 200, {"ok": True, "already_running": False, "started": True}


def known_instance(name: str) -> bool:
    if not HCOM_NAME_RE.match(name or ""):
        return False
    try:
        con = hcom_connect()
        try:
            row = con.execute("SELECT 1 FROM instances WHERE name = ?", (name,)).fetchone()
        finally:
            con.close()
        return row is not None
    except Exception:
        return False


def term_screen(name: str) -> tuple[int, dict]:
    if not known_instance(name):
        return 400, {"ok": False, "error": "unknown agent name"}
    try:
        proc = subprocess.run(
            ["hcom", "term", name, "--json"],
            cwd=str(WORKSPACE),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except Exception as exc:
        return 500, {"ok": False, "error": str(exc)}
    if proc.returncode != 0:
        return 502, {"ok": False, "error": proc.stderr.strip() or "hcom term failed"}
    try:
        screen = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return 502, {"ok": False, "error": "unparseable hcom term output", "raw": proc.stdout[:400]}
    return 200, {"ok": True, "name": name, "screen": screen}


def term_inject(payload: dict) -> tuple[int, dict]:
    name = payload.get("name")
    text = payload.get("text", "")
    enter = bool(payload.get("enter"))
    if not isinstance(name, str) or not known_instance(name):
        return 400, {"ok": False, "error": "unknown agent name"}
    if not isinstance(text, str):
        return 400, {"ok": False, "error": "text must be a string"}
    if len(text) > 500:
        return 400, {"ok": False, "error": "inject text too long (500 chars max)"}
    if not text and not enter:
        return 400, {"ok": False, "error": "nothing to inject"}

    cmd = ["hcom", "term", "inject", name]
    if text:
        cmd.append(text)
    if enter:
        cmd.append("--enter")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(WORKSPACE),
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except Exception as exc:
        return 500, {"ok": False, "error": str(exc)}

    # Durable audit trail: every keystroke the UI puts into an agent terminal.
    audit_path = PROJECT_DIR / "runtime" / "inject-audit.jsonl"
    try:
        audit_path.parent.mkdir(exist_ok=True)
        with audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "operator": OPERATOR_NAME,
                "target": name,
                "text": text,
                "enter": enter,
                "returncode": proc.returncode,
            }) + "\n")
    except Exception:
        pass

    ok = proc.returncode == 0
    return (200 if ok else 502), {
        "ok": ok,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def map_connect():
    import sqlite3

    return sqlite3.connect(MAP_DIR / "map.db", timeout=5)


def read_approvals() -> dict:
    """Pending MAP approval gates + agent terminals sitting on a prompt."""
    gates = []
    try:
        con = map_connect()
        try:
            rows = con.execute(
                "SELECT gate_id, name, required_after_task, created_at"
                " FROM approval_gates WHERE status='pending' ORDER BY rowid",
            ).fetchall()
        finally:
            con.close()
        gates = [
            {"gate_id": g, "name": n, "after_task": t, "created_at": c}
            for g, n, t, c in rows
        ]
    except Exception:
        pass
    prompts = []
    try:
        con = hcom_connect()
        try:
            rows = con.execute(
                "SELECT name, tag, status_context, status_time FROM instances"
                " WHERE status='blocked' ORDER BY status_time DESC",
            ).fetchall()
        finally:
            con.close()
        now = time.time()
        for name, tag, context, status_time in rows:
            age = max(0, int(now - status_time)) if status_time else None
            if age is not None and age > 3600:
                continue  # stale session, not a live prompt
            prompts.append({
                "name": name, "tag": tag or "",
                "context": context or "", "age_seconds": age,
            })
    except Exception:
        pass
    return {"ok": True, "gates": gates, "prompts": prompts}


def decide_gate(payload: dict) -> tuple[int, dict]:
    """Explicit operator decision on a MAP approval gate.

    Same UPDATE the LangGraph runner's _record_gate_decision performs, plus
    approved_by for the audit trail. Never called without an operator click.
    """
    gate_id = payload.get("gate_id")
    approve = payload.get("approve")
    if not isinstance(gate_id, str) or not re.match(r"^[A-Za-z0-9_-]{1,64}$", gate_id):
        return 400, {"ok": False, "error": "invalid gate_id"}
    if not isinstance(approve, bool):
        return 400, {"ok": False, "error": "approve must be true or false"}
    status = "approved" if approve else "rejected"
    try:
        con = map_connect()
        try:
            cursor = con.execute(
                "UPDATE approval_gates SET status=?, approved_by=?,"
                " approved_at=datetime('now') WHERE gate_id=? AND status='pending'",
                (status, OPERATOR_NAME, gate_id),
            )
            con.commit()
            changed = cursor.rowcount
        finally:
            con.close()
    except Exception as exc:
        return 500, {"ok": False, "error": str(exc)}
    if changed != 1:
        return 409, {"ok": False, "error": "gate not found or not pending"}
    audit_path = PROJECT_DIR / "runtime" / "gate-audit.jsonl"
    try:
        audit_path.parent.mkdir(exist_ok=True)
        with audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({
                "at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "operator": OPERATOR_NAME,
                "gate_id": gate_id,
                "decision": status,
            }) + "\n")
    except Exception:
        pass
    return 200, {"ok": True, "gate_id": gate_id, "status": status}


def hcom_list() -> dict:
    if HCOM_AGENT_NAME == "browser":
        return {
            "ok": False,
            "mode": "browser",
            "identity": HCOM_AGENT_NAME,
            "text": "",
            "error": "Read-only browser mode. Start with COMMAND_CENTER_UI_AGENT_NAME=<registered_hcom_name> to enable hcom send/list.",
        }
    try:
        proc = subprocess.run(
            ["hcom", "list", "--name", HCOM_AGENT_NAME],
            cwd=str(WORKSPACE),
            text=True,
            capture_output=True,
            timeout=5,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "mode": "identity",
            "identity": HCOM_AGENT_NAME,
            "text": proc.stdout.strip(),
            "error": proc.stderr.strip(),
        }
    except Exception as exc:
        return {"ok": False, "mode": "identity", "identity": HCOM_AGENT_NAME, "text": "", "error": str(exc)}


def send_hcom(payload: dict) -> tuple[int, dict]:
    if HCOM_AGENT_NAME == "browser":
        return 403, {
            "ok": False,
            "error": "No hcom identity configured. Restart with COMMAND_CENTER_UI_AGENT_NAME=<registered_hcom_name> to send.",
        }
    recipients = payload.get("recipients")
    intent = payload.get("intent")
    body = payload.get("body")
    reply_to = payload.get("reply_to")

    if not isinstance(recipients, list) or not recipients:
        return 400, {"ok": False, "error": "recipients must be a non-empty list"}
    cleaned = []
    for recipient in recipients:
        if not isinstance(recipient, str) or not RECIPIENT_RE.match(recipient):
            return 400, {"ok": False, "error": f"invalid recipient: {recipient!r}"}
        cleaned.append(recipient if recipient.startswith("@") else f"@{recipient}")
    if intent not in INTENTS:
        return 400, {"ok": False, "error": "intent must be request, inform, or ack"}
    if not isinstance(body, str) or not body.strip():
        return 400, {"ok": False, "error": "body is required"}
    if len(body) > 4000:
        return 400, {"ok": False, "error": "body is too long"}

    cmd = ["hcom", "send", *cleaned, "--intent", intent, "--name", HCOM_AGENT_NAME]
    if reply_to:
        if not str(reply_to).replace(":", "").isalnum():
            return 400, {"ok": False, "error": "reply_to must be an hcom id"}
        cmd.extend(["--reply-to", str(reply_to)])
    cmd.extend(["--", body])

    try:
        proc = subprocess.run(
            cmd,
            cwd=str(WORKSPACE),
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
        return 200 if proc.returncode == 0 else 502, {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "returncode": proc.returncode,
        }
    except Exception as exc:
        return 500, {"ok": False, "error": str(exc)}


class Handler(SimpleHTTPRequestHandler):
    server_version = "CommandCenterUI/0.1"

    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        rel = parsed.path.lstrip("/")
        if rel == "":
            rel = "chat.html"
        target = (SRC_DIR / rel).resolve()
        try:
            target.relative_to(SRC_DIR.resolve())
        except ValueError:
            return str(SRC_DIR / "chat.html")
        return str(target)

    def log_message(self, format: str, *args) -> None:
        stamp = time.strftime("%H:%M:%S")
        print(f"[{stamp}] {self.address_string()} {format % args}")

    def write_json(self, status: int, payload: dict | list) -> None:
        data = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def allowed_origins(self) -> set[str]:
        host = self.headers.get("Host", "")
        server_host, server_port = self.server.server_address[:2]
        candidates = {
            host,
            f"{server_host}:{server_port}",
            f"127.0.0.1:{server_port}",
            f"localhost:{server_port}",
        }
        return {f"http://{candidate}" for candidate in candidates if candidate}

    def same_origin_request(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is not None:
            return origin in self.allowed_origins()
        referer = self.headers.get("Referer")
        if referer:
            parsed = urlparse(referer)
            if not parsed.scheme or not parsed.netloc:
                return False
            return f"{parsed.scheme}://{parsed.netloc}" in self.allowed_origins()
        return True

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/project-updater" or parsed.path.startswith("/project-updater/"):
            asset = project_updater_asset(parsed.path)
            if not asset:
                self.write_json(404, {"ok": False, "error": "ProjectUpdater asset not found"})
                return
            ctype = mimetypes.guess_type(str(asset))[0] or "text/html"
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(asset.stat().st_size))
            self.end_headers()
            with asset.open("rb") as handle:
                self.wfile.write(handle.read())
            return
        if parsed.path == "/api/snapshot":
            query = parse_qs(parsed.query)
            try:
                limit = bounded_int(query.get("limit", ["40"])[0], default=40, lower=1, upper=200)
            except ValueError:
                self.write_json(400, {"ok": False, "error": "limit must be an integer"})
                return
            self.write_json(200, {
                "ok": True,
                "project_dir": str(PROJECT_DIR),
                "workspace": str(WORKSPACE),
                "events": read_events(limit),
                "tasks": task_summary(),
                "agents_status": read_json(AGENTS_STATUS_PATH, {}),
                "hcom": hcom_list(),
            })
            return
        if parsed.path == "/api/chat":
            query = parse_qs(parsed.query)
            try:
                since = bounded_int(query.get("since", ["0"])[0], default=0, lower=0, upper=2**53)
                limit = bounded_int(query.get("limit", ["100"])[0], default=100, lower=1, upper=500)
            except ValueError:
                self.write_json(400, {"ok": False, "error": "since/limit must be integers"})
                return
            self.write_json(200, read_chat(since, limit))
            return
        if parsed.path == "/api/presence":
            query = parse_qs(parsed.query)
            force_usage = query.get("refresh", ["0"])[0] in {"1", "true", "yes"}
            self.write_json(200, read_presence(force_usage=force_usage))
            return
        if parsed.path == "/api/lab/status":
            self.write_json(200, lab_status())
            return
        if parsed.path == "/api/attention":
            self.write_json(200, read_attention())
            return
        if parsed.path == "/api/approvals":
            self.write_json(200, read_approvals())
            return
        if parsed.path == "/api/summaries":
            query = parse_qs(parsed.query)
            try:
                since = bounded_int(query.get("since", ["0"])[0], default=0, lower=0, upper=2**53)
            except ValueError:
                self.write_json(400, {"ok": False, "error": "since must be an integer"})
                return
            self.write_json(200, {
                "ok": True,
                "available": SUMMARIZER.available,
                "summaries": SUMMARIZER.recent(since),
            })
            return
        if parsed.path == "/api/term":
            query = parse_qs(parsed.query)
            name = query.get("name", [""])[0]
            status, result = term_screen(name)
            self.write_json(status, result)
            return
        if parsed.path == "/api/events":
            query = parse_qs(parsed.query)
            try:
                limit = bounded_int(query.get("limit", ["80"])[0], default=80, lower=1, upper=500)
            except ValueError:
                self.write_json(400, {"ok": False, "error": "limit must be an integer"})
                return
            self.write_json(200, {"ok": True, "events": read_events(limit)})
            return
        if parsed.path == "/api/map/health":
            query = parse_qs(parsed.query)
            force = query.get("refresh", ["0"])[0] in {"1", "true", "yes"}
            self.write_json(200, map_health(force=force))
            return
        if parsed.path == "/api/tasks":
            self.write_json(200, {"ok": True, **task_summary()})
            return
        if parsed.path == "/api/project-updater/status":
            self.write_json(200, read_project_updater_status())
            return
        if parsed.path == "/api/agents":
            self.write_json(200, {"ok": True, "hcom": hcom_list(), "status": read_json(AGENTS_STATUS_PATH, {})})
            return
        return super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path not in {
            "/api/hcom/send",
            "/api/chat/send",
            "/api/lab/start",
            "/api/term/inject",
            "/api/gate/decide",
            "/api/project-updater/open",
            "/api/local-agent/launch",
            "/api/usage/refresh",
        }:
            self.write_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "not found"})
            return
        if not self.same_origin_request():
            self.write_json(403, {"ok": False, "error": "cross-origin hcom send rejected"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.write_json(400, {"ok": False, "error": "Content-Length must be an integer"})
            return
        if length > 12000:
            self.write_json(413, {"ok": False, "error": "payload too large"})
            return
        try:
            body = self.rfile.read(length)
            payload = json.loads(body) if body.strip() else {}
        except Exception:
            self.write_json(400, {"ok": False, "error": "invalid json"})
            return
        if parsed.path == "/api/chat/send":
            status, result = send_chat(payload)
        elif parsed.path == "/api/lab/start":
            status, result = start_lab()
        elif parsed.path == "/api/term/inject":
            status, result = term_inject(payload)
        elif parsed.path == "/api/gate/decide":
            status, result = decide_gate(payload)
        elif parsed.path == "/api/project-updater/open":
            status, result = open_project_updater()
        elif parsed.path == "/api/local-agent/launch":
            status, result = launch_local_agent(payload)
        elif parsed.path == "/api/usage/refresh":
            presence = read_presence(force_usage=True)
            status, result = 200, {
                "ok": True,
                "presence": presence,
                "health": map_health(force=True),
                "rns_sync": sync_rns_provider_limits(presence.get("provider_usage") or {}),
            }
        else:
            status, result = send_hcom(payload)
        self.write_json(status, result)


def main() -> int:
    global HCOM_AGENT_NAME
    parser = argparse.ArgumentParser(description="Run the local CommandCenterUI app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--agent-name",
        default=os.environ.get("COMMAND_CENTER_UI_AGENT_NAME", "browser"),
        help="hcom identity used by this UI for list/send operations",
    )
    args = parser.parse_args()
    if args.agent_name != "browser" and not HCOM_NAME_RE.match(args.agent_name):
        parser.error("--agent-name must be browser or contain only lowercase letters, numbers, or _")
    HCOM_AGENT_NAME = args.agent_name

    mimetypes.add_type("text/javascript", ".js")
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"CommandCenterUI listening on http://{args.host}:{args.port}/")
    print(f"hcom identity: {HCOM_AGENT_NAME}")
    print(f"Project files: {PROJECT_DIR}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping CommandCenterUI")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
