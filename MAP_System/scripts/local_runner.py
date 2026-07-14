#!/usr/bin/env python3
"""Scoped Ollama helper runner with durable MAP records."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.event_trace import add_trace_fields
from MAP_System.scripts.local_assistant_health import REQUIRED_MODELS, build_report

EVENT_LOG = ROOT / "events" / "events.jsonl"
HELPERS_DIR = ROOT / "inbox" / "helpers"


class LocalRunnerError(RuntimeError):
    pass


def utc_stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def slug(text: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(part for part in safe.split("-") if part)[:80] or "local-helper"


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt and args.prompt_file:
        raise LocalRunnerError("use either --prompt or --prompt-file, not both")
    if args.prompt_file:
        return args.prompt_file.read_text(encoding="utf-8")
    if args.prompt:
        return args.prompt
    raise LocalRunnerError("one of --prompt or --prompt-file is required")


def validate_model(model: str) -> None:
    if model not in REQUIRED_MODELS:
        allowed = ", ".join(REQUIRED_MODELS)
        raise LocalRunnerError(f"model '{model}' is not allowed; allowed models: {allowed}")


def check_health(model: str, timeout: float) -> None:
    report = build_report(timeout)
    if not report["ollama"]["reachable"]:
        raise LocalRunnerError("ollama is not reachable")
    available = {
        item["name"]
        for item in report["ollama"]["models"]
        if item["available"]
    }
    if model not in available:
        raise LocalRunnerError(f"required model '{model}' is not available locally")


def run_ollama(model: str, prompt: str, timeout: float) -> str:
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise LocalRunnerError(f"ollama run timed out after {timeout:g}s") from exc
    if result.returncode != 0:
        detail = result.stderr.strip() or f"exit {result.returncode}"
        raise LocalRunnerError(f"ollama run failed: {detail}")
    return result.stdout


def write_helper_note(
    *,
    task_id: str,
    model: str,
    scope: str,
    prompt_source: str,
    output_path: Path,
    note_dir: Path,
) -> Path:
    note_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()
    path = note_dir / f"{slug(task_id)}-{slug(model)}-{stamp.replace(':', '')}.md"
    path.write_text(
        "\n".join(
            [
                f"# Local Helper Invocation: {task_id}",
                "",
                f"- task_id: {task_id}",
                f"- model: {model}",
                f"- scope: {scope}",
                f"- prompt_source: {prompt_source}",
                f"- output_path: {output_path}",
                f"- invoked_at: {stamp}",
                "",
                "This is a helper-capability record. The local model does not own task",
                "completion, approval, release, or final architecture decisions.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def append_event(event_log: Path, *, task_id: str, model: str, note_path: Path, output_path: Path) -> None:
    event_log.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": utc_stamp(),
        "type": "PROGRESS",
        "task_id": task_id,
        "sender": "local_runner",
        "summary": f"Local model helper invoked: {model}",
        "artifact_paths": [str(note_path), str(output_path)],
    }
    add_trace_fields(payload, actor="local_runner", action="helper_invoked", target=task_id)
    with event_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")


def run(args: argparse.Namespace) -> dict[str, str]:
    validate_model(args.model)
    prompt = read_prompt(args)
    output_path = args.output
    check_health(args.model, args.health_timeout)
    response = run_ollama(args.model, prompt, args.run_timeout)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response, encoding="utf-8")
    prompt_source = str(args.prompt_file) if args.prompt_file else "inline"
    note_path = write_helper_note(
        task_id=args.task_id,
        model=args.model,
        scope=args.scope,
        prompt_source=prompt_source,
        output_path=output_path,
        note_dir=args.helper_dir,
    )
    append_event(args.event_log, task_id=args.task_id, model=args.model, note_path=note_path, output_path=output_path)
    return {"output": str(output_path), "helper_note": str(note_path)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--event-log", type=Path, default=EVENT_LOG)
    parser.add_argument("--helper-dir", type=Path, default=HELPERS_DIR)
    parser.add_argument("--health-timeout", type=float, default=5.0)
    parser.add_argument("--run-timeout", type=float, default=120.0)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = run(args)
    except (LocalRunnerError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
