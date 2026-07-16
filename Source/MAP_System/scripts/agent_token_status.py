#!/usr/bin/env python3
"""Read-only agent token and rate-limit status from hcom transcript files.

Codex session JSONL includes explicit token_count/rate_limits events, so Codex
percent-used can be reported directly. Claude Code session JSONL includes
per-response message.usage records but does not expose the subscription
remaining-percent; for Claude this reports observed transcript token totals and
detects recorded rate-limit reset messages.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
CLAUDE_PROJECT_DIR = Path.home() / ".claude" / "projects" / "-home-home-Projects-MultiAgentProject"


def _read_jsonl(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _hcom_list() -> list[dict[str, Any]]:
    try:
        result = subprocess.run(
            ["hcom", "list", "--json"],
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def _human_int(value: int | None) -> str:
    if value is None:
        return "-"
    return f"{value:,}"


def _fmt_time(epoch: int | float | None) -> str:
    if not epoch:
        return "-"
    try:
        return datetime.fromtimestamp(float(epoch), timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    except (OSError, ValueError, OverflowError):
        return str(epoch)


def _resolve_transcript(agent: dict[str, Any]) -> Path | None:
    raw_path = agent.get("transcript_path")
    if isinstance(raw_path, str) and raw_path:
        path = Path(raw_path)
        if path.exists():
            return path
    if agent.get("tool") == "claude":
        session_id = agent.get("session_id")
        if session_id:
            fallback = CLAUDE_PROJECT_DIR / f"{session_id}.jsonl"
            if fallback.exists():
                return fallback
    return None


def _codex_metrics(path: Path) -> dict[str, Any]:
    last = None
    model = None
    model_provider = None
    cli_version = None
    for event in _read_jsonl(path):
        if event.get("type") == "session_meta":
            payload = event.get("payload") or {}
            model = payload.get("model") or model
            model_provider = payload.get("model_provider") or model_provider
            cli_version = payload.get("cli_version") or cli_version
        if event.get("type") != "event_msg":
            continue
        payload = event.get("payload") or {}
        if payload.get("type") == "token_count":
            last = {"timestamp": event.get("timestamp"), **payload}
    if not last:
        return {"available": False}
    info = last.get("info") or {}
    usage = info.get("total_token_usage") or {}
    last_usage = info.get("last_token_usage") or {}
    limits = last.get("rate_limits") or {}
    primary = limits.get("primary") or {}
    secondary = limits.get("secondary") or {}
    return {
        "available": True,
        "model": model,
        "model_provider": model_provider,
        "model_label": model or ("Codex / OpenAI" if model_provider == "openai" else "Codex"),
        "cli_version": cli_version,
        "timestamp": last.get("timestamp"),
        "total_tokens": usage.get("total_tokens"),
        "input_tokens": usage.get("input_tokens"),
        "cached_input_tokens": usage.get("cached_input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "last_tokens": last_usage.get("total_tokens"),
        "context_window": info.get("model_context_window"),
        "primary_used_percent": primary.get("used_percent"),
        "primary_resets_at": primary.get("resets_at"),
        "secondary_used_percent": secondary.get("used_percent"),
        "secondary_resets_at": secondary.get("resets_at"),
        "plan_type": limits.get("plan_type"),
        "rate_limit_reached_type": limits.get("rate_limit_reached_type"),
    }


def _usage_total(usage: dict[str, Any]) -> dict[str, int]:
    return {
        "input_tokens": int(usage.get("input_tokens") or 0),
        "cache_creation_input_tokens": int(usage.get("cache_creation_input_tokens") or 0),
        "cache_read_input_tokens": int(usage.get("cache_read_input_tokens") or 0),
        "output_tokens": int(usage.get("output_tokens") or 0),
    }


RESET_RE = re.compile(r"resets\s+(\d{1,2}):(\d{2})\s*([ap]m)\s*\(([^)]+)\)", re.IGNORECASE)


def _parse_iso_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _active_limit(limit: dict[str, Any] | None) -> dict[str, Any] | None:
    if not limit:
        return None
    text = str(limit.get("text") or "")
    match = RESET_RE.search(text)
    if not match:
        return limit
    event_time = _parse_iso_time(limit.get("timestamp"))
    if event_time is None:
        return limit
    try:
        zone = ZoneInfo(match.group(4))
    except Exception:
        return limit
    hour = int(match.group(1))
    minute = int(match.group(2))
    meridiem = match.group(3).lower()
    if meridiem == "pm" and hour != 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0
    event_local = event_time.astimezone(zone)
    reset = event_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if reset <= event_local:
        reset += timedelta(days=1)
    if datetime.now(zone) >= reset:
        return None
    return {**limit, "reset_at": reset.isoformat()}


def _claude_metrics(path: Path) -> dict[str, Any]:
    totals = {
        "input_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "output_tokens": 0,
    }
    seen_requests: set[str] = set()
    turns = 0
    last_usage_at = None
    limit = None
    model = None
    for event in _read_jsonl(path):
        message = event.get("message") or {}
        if isinstance(message, dict) and message.get("model") and message.get("model") != "<synthetic>":
            model = message.get("model")
        usage = message.get("usage")
        request_id = event.get("requestId") or message.get("id") or event.get("uuid")
        if isinstance(usage, dict) and request_id and request_id not in seen_requests:
            seen_requests.add(str(request_id))
            if event.get("isApiErrorMessage") or event.get("error") == "rate_limit":
                text = ""
                for item in message.get("content") or []:
                    if isinstance(item, dict):
                        text += item.get("text") or ""
                limit = {
                    "timestamp": event.get("timestamp"),
                    "text": " ".join(text.split()),
                }
                continue
            part = _usage_total(usage)
            for key, value in part.items():
                totals[key] += value
            turns += 1
            last_usage_at = event.get("timestamp")
            # A later successful Claude response means an earlier session-limit
            # note in the same transcript is no longer the current state.
            limit = None
    observed_total = sum(totals.values())
    billableish = totals["input_tokens"] + totals["cache_creation_input_tokens"] + totals["output_tokens"]
    return {
        "available": True,
        "model": model,
        "model_label": model or "Claude",
        "timestamp": last_usage_at,
        "turns": turns,
        "total_tokens": observed_total,
        "non_cached_tokens": billableish,
        "input_tokens": totals["input_tokens"],
        "cache_creation_input_tokens": totals["cache_creation_input_tokens"],
        "cache_read_input_tokens": totals["cache_read_input_tokens"],
        "output_tokens": totals["output_tokens"],
        "limit": _active_limit(limit),
    }


def _claude_recent_transcripts(*, exclude: set[Path], recent_hours: int) -> list[dict[str, Any]]:
    """Return recent Claude project transcripts not already tied to hcom.

    hcom can occasionally point at a Claude session_id whose JSONL file does
    not exist locally, while Claude Code still has other recent project JSONL
    files. Reporting those as unattached keeps the token count visible without
    inventing an agent-name mapping.
    """
    if not CLAUDE_PROJECT_DIR.exists():
        return []
    cutoff = datetime.now().timestamp() - (recent_hours * 3600)
    rows = []
    for path in sorted(CLAUDE_PROJECT_DIR.glob("*.jsonl"), key=lambda p: p.stat().st_mtime):
        resolved = path.resolve()
        if resolved in exclude:
            continue
        stat = path.stat()
        if stat.st_mtime < cutoff:
            continue
        metrics = _claude_metrics(path)
        if not metrics.get("available") or not metrics.get("total_tokens"):
            continue
        rows.append({
            "path": str(path),
            "mtime": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "metrics": metrics,
        })
    return rows


def build_status(*, recent_hours: int = 24) -> dict[str, Any]:
    agents = []
    used_paths: set[Path] = set()
    totals = {
        "codex_total_tokens": 0,
        "claude_attached_total_tokens": 0,
        "claude_attached_non_cached_tokens": 0,
        "claude_unattached_recent_total_tokens": 0,
        "claude_unattached_recent_non_cached_tokens": 0,
        "claude_total_tokens": 0,
        "claude_non_cached_tokens": 0,
    }
    for agent in _hcom_list():
        tool = agent.get("tool") or "unknown"
        path = _resolve_transcript(agent)
        row: dict[str, Any] = {
            "name": agent.get("name"),
            "tool": tool,
            "status": agent.get("status"),
            "process_bound": agent.get("process_bound"),
            "transcript_path": str(path) if path else agent.get("transcript_path"),
            "transcript_found": bool(path),
        }
        if path:
            used_paths.add(path.resolve())
        if path and tool == "codex":
            row["metrics"] = _codex_metrics(path)
            if row["metrics"].get("total_tokens"):
                totals["codex_total_tokens"] += int(row["metrics"]["total_tokens"])
        elif path and tool == "claude":
            row["metrics"] = _claude_metrics(path)
            totals["claude_attached_total_tokens"] += int(row["metrics"].get("total_tokens") or 0)
            totals["claude_attached_non_cached_tokens"] += int(row["metrics"].get("non_cached_tokens") or 0)
        else:
            row["metrics"] = {"available": False}
        agents.append(row)

    unattached = _claude_recent_transcripts(exclude=used_paths, recent_hours=recent_hours)
    for item in unattached:
        metrics = item["metrics"]
        totals["claude_unattached_recent_total_tokens"] += int(metrics.get("total_tokens") or 0)
        totals["claude_unattached_recent_non_cached_tokens"] += int(metrics.get("non_cached_tokens") or 0)
    totals["claude_total_tokens"] = (
        totals["claude_attached_total_tokens"] + totals["claude_unattached_recent_total_tokens"]
    )
    totals["claude_non_cached_tokens"] = (
        totals["claude_attached_non_cached_tokens"] + totals["claude_unattached_recent_non_cached_tokens"]
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "recent_hours": recent_hours,
        "totals": totals,
        "agents": agents,
        "unattached_recent_claude_transcripts": unattached,
    }


def print_text(status: dict[str, Any]) -> None:
    print("Agent Token Status")
    print(status["generated_at"])
    print()
    totals = status["totals"]
    print(f"Totals: codex={_human_int(totals['codex_total_tokens'])} tokens | "
          f"claude observed={_human_int(totals['claude_total_tokens'])} tokens "
          f"(attached={_human_int(totals['claude_attached_total_tokens'])}, "
          f"unattached-recent={_human_int(totals['claude_unattached_recent_total_tokens'])}, "
          f"non-cached={_human_int(totals['claude_non_cached_tokens'])})")
    print()
    for agent in status["agents"]:
        name = agent.get("name") or "?"
        tool = agent.get("tool") or "?"
        live = "live" if agent.get("process_bound") else "not process-bound"
        print(f"{name} [{tool}] {agent.get('status') or '?'}; {live}")
        if not agent.get("transcript_found"):
            print(f"  transcript: missing ({agent.get('transcript_path') or 'none'})")
            continue
        metrics = agent.get("metrics") or {}
        if tool == "codex" and metrics.get("available"):
            print(f"  tokens: total={_human_int(metrics.get('total_tokens'))} "
                  f"last={_human_int(metrics.get('last_tokens'))} "
                  f"context={_human_int(metrics.get('context_window'))}")
            primary = metrics.get("primary_used_percent")
            secondary = metrics.get("secondary_used_percent")
            print(f"  limit: primary={primary if primary is not None else '-'}% "
                  f"resets={_fmt_time(metrics.get('primary_resets_at'))}; "
                  f"secondary={secondary if secondary is not None else '-'}% "
                  f"resets={_fmt_time(metrics.get('secondary_resets_at'))}")
        elif tool == "claude" and metrics.get("available"):
            print(f"  tokens: observed={_human_int(metrics.get('total_tokens'))} "
                  f"non-cached={_human_int(metrics.get('non_cached_tokens'))} "
                  f"turns={metrics.get('turns')}")
            print(f"  cache: create={_human_int(metrics.get('cache_creation_input_tokens'))} "
                  f"read={_human_int(metrics.get('cache_read_input_tokens'))}; "
                  f"output={_human_int(metrics.get('output_tokens'))}")
            limit = metrics.get("limit")
            if limit:
                print(f"  limit: {limit.get('text') or 'rate limited'} at {limit.get('timestamp')}")
            else:
                print("  limit: percent remaining is not exposed in Claude transcript data")
        else:
            print("  metrics: no token records found")
    unattached = status.get("unattached_recent_claude_transcripts") or []
    if unattached:
        print()
        print(f"Unattached recent Claude transcripts ({status.get('recent_hours')}h, not mapped to hcom name):")
        for item in unattached:
            metrics = item.get("metrics") or {}
            print(f"  {Path(item.get('path', '?')).name} mtime={item.get('mtime')}")
            print(f"    tokens: observed={_human_int(metrics.get('total_tokens'))} "
                  f"non-cached={_human_int(metrics.get('non_cached_tokens'))} "
                  f"turns={metrics.get('turns')}")
            limit = metrics.get("limit")
            if limit:
                print(f"    limit: {limit.get('text') or 'rate limited'} at {limit.get('timestamp')}")
    print()
    print("Note: Claude totals are transcript usage, not a remaining-limit percentage. "
          "Codex exposes used_percent directly. Unattached Claude transcripts are included "
          "in Claude totals but not assigned to a live hcom agent.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--recent-hours",
        type=int,
        default=24,
        help="include unattached Claude project transcripts modified within this many hours",
    )
    args = parser.parse_args()
    status = build_status(recent_hours=max(args.recent_hours, 0))
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True))
    else:
        print_text(status)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
