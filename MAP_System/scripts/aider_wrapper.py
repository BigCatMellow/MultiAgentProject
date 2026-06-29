#!/usr/bin/env python3
"""Prepare a scoped, interactive Aider helper session."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
TASKS_DIR = ROOT / "tasks"
HELPERS_DIR = ROOT / "inbox" / "helpers"
EVENT_LOG = ROOT / "events" / "events.jsonl"
FORBIDDEN_AIDER_FLAGS = {"--yes-always", "--yes", "--auto-commits"}


class AiderWrapperError(RuntimeError):
    pass


def utc_stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def slug(text: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in text)
    return "-".join(part for part in safe.split("-") if part)[:80] or "aider-helper"


def load_task(task_id: str, tasks_dir: Path = TASKS_DIR) -> dict:
    path = tasks_dir / f"{task_id}.json"
    if not path.exists():
        raise AiderWrapperError(f"task file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def normalize(path: str | Path) -> str:
    return Path(path).as_posix().rstrip("/")


def path_in_scope(target: Path, output_paths: list[str]) -> bool:
    target_norm = normalize(target)
    for output in output_paths:
        scope = normalize(output)
        if target_norm == scope or target_norm.startswith(scope + "/"):
            return True
    return False


def validate_targets(task: dict, targets: list[Path]) -> None:
    output_paths = [str(path) for path in task.get("output_paths", [])]
    if not output_paths:
        raise AiderWrapperError(f"{task.get('task_id', '<unknown>')} has no output_paths")
    out_of_scope = [str(target) for target in targets if not path_in_scope(target, output_paths)]
    if out_of_scope:
        raise AiderWrapperError("target file outside task output_paths: " + ", ".join(out_of_scope))


def dirty_target_files(targets: list[Path], *, repo: Path = REPO) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(repo), "status", "--porcelain", "--", *[str(target) for target in targets]],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        raise AiderWrapperError(result.stderr.strip() or "git status failed")
    dirty: list[str] = []
    for line in result.stdout.splitlines():
        if line.strip():
            dirty.append(line[3:].strip() if len(line) > 3 else line.strip())
    return dirty


def validate_aider_args(args: list[str]) -> None:
    bad = [arg for arg in args if arg in FORBIDDEN_AIDER_FLAGS or arg.startswith("--yes-always=")]
    if bad:
        raise AiderWrapperError("forbidden Aider flag(s): " + ", ".join(bad))


def write_helper_note(
    *,
    task_id: str,
    intent: str,
    targets: list[Path],
    aider_args: list[str],
    helper_dir: Path,
) -> Path:
    helper_dir.mkdir(parents=True, exist_ok=True)
    stamp = utc_stamp()
    path = helper_dir / f"{slug(task_id)}-aider-{stamp.replace(':', '')}.md"
    target_lines = "\n".join(f"- `{target}`" for target in targets)
    arg_text = " ".join(aider_args) if aider_args else "(none)"
    path.write_text(
        "\n".join(
            [
                f"# Aider Helper Setup: {task_id}",
                "",
                f"- task_id: {task_id}",
                f"- intent: {intent}",
                f"- launched_at: {stamp}",
                f"- aider_args: {arg_text}",
                "",
                "## Target Files",
                "",
                target_lines,
                "",
                "This wrapper only prepares an interactive Aider session. It does not",
                "auto-apply edits, approve changes, or replace operator judgment.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def append_event(event_log: Path, *, task_id: str, note_path: Path, targets: list[Path]) -> None:
    event_log.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "created_at": utc_stamp(),
        "type": "HELPER_INVOKED",
        "task_id": task_id,
        "sender": "aider_wrapper",
        "summary": "Interactive Aider helper session prepared",
        "artifact_paths": [str(note_path), *[str(target) for target in targets]],
    }
    with event_log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")


def launch_aider(targets: list[Path], aider_args: list[str]) -> int:
    cmd = ["aider", *aider_args, *[str(target) for target in targets]]
    return subprocess.call(cmd, cwd=REPO)


def split_wrapper_and_aider_args(argv: list[str] | None) -> tuple[list[str] | None, list[str]]:
    if argv is None:
        argv = sys.argv[1:]
    if "--" not in argv:
        return argv, []
    index = argv.index("--")
    return argv[:index], argv[index + 1:]


def run(args: argparse.Namespace, aider_args: list[str]) -> int:
    task = load_task(args.task_id, args.tasks_dir)
    targets = args.target
    if not targets:
        raise AiderWrapperError("at least one --target is required")
    validate_targets(task, targets)
    dirty = dirty_target_files(targets, repo=args.repo)
    if dirty:
        raise AiderWrapperError("target file has uncommitted changes: " + ", ".join(dirty))
    validate_aider_args(aider_args)
    note_path = write_helper_note(
        task_id=args.task_id,
        intent=args.intent,
        targets=targets,
        aider_args=aider_args,
        helper_dir=args.helper_dir,
    )
    append_event(args.event_log, task_id=args.task_id, note_path=note_path, targets=targets)
    if args.dry_run:
        print(json.dumps({"helper_note": str(note_path), "dry_run": True}, separators=(",", ":")))
        return 0
    return launch_aider(targets, aider_args)


def parse_args(argv: list[str] | None = None) -> tuple[argparse.Namespace, list[str]]:
    wrapper_args, aider_args = split_wrapper_and_aider_args(argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--intent", required=True)
    parser.add_argument("--target", type=Path, action="append", default=[])
    parser.add_argument("--tasks-dir", type=Path, default=TASKS_DIR)
    parser.add_argument("--helper-dir", type=Path, default=HELPERS_DIR)
    parser.add_argument("--event-log", type=Path, default=EVENT_LOG)
    parser.add_argument("--repo", type=Path, default=REPO)
    parser.add_argument("--dry-run", action="store_true", help="Validate and write records without launching Aider")
    return parser.parse_args(wrapper_args), aider_args


def main(argv: list[str] | None = None) -> int:
    try:
        args, aider_args = parse_args(argv)
        return run(args, aider_args)
    except (AiderWrapperError, OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
