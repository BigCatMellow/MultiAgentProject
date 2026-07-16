#!/usr/bin/env python3
"""Generate ProjectUpdater command URLs for Command Center integrations."""

from __future__ import annotations

import argparse
import base64
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen


PROJECT_UPDATER_DIR = Path(__file__).resolve().parents[1]
APP_PATH = PROJECT_UPDATER_DIR / "app" / "index.html"
PRIORITIES = {"Low", "Medium", "High"}
STATUSES = {"Not started", "Active", "In progress", "Finished", "Archived"}
NOTE_TYPES = {"Note", "Idea", "Decision", "Blocker", "Next Action"}
COMMAND_CENTER_STATUS_URL = "http://127.0.0.1:8765/api/project-updater/status"
COMMAND_CENTER_APP_URL = "http://127.0.0.1:8765/project-updater/"


def file_url(path: Path) -> str:
    return "file://" + quote(str(path), safe="/:")


def command_center_available() -> bool:
    try:
        with urlopen(COMMAND_CENTER_STATUS_URL, timeout=0.4) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return False
    return bool(data.get("ok") and data.get("app_exists"))


def base_app_url(target: str) -> str:
    if target == "command-center":
        return COMMAND_CENTER_APP_URL
    if target == "standalone":
        return file_url(APP_PATH)
    if command_center_available():
        return COMMAND_CENTER_APP_URL
    return file_url(APP_PATH)


def encode_command(action: str, payload: dict, *, target: str) -> str:
    command = {
        "source": "AI Command Center",
        "version": 1,
        "action": action,
        "payload": {key: value for key, value in payload.items() if value is not None},
    }
    raw = json.dumps(command, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    token = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    return f"{base_app_url(target)}#cc={token}"


def maybe_open(url: str, *, url_only: bool) -> int:
    if url_only:
        print(url)
        return 0
    if not APP_PATH.exists():
        print(f"ProjectUpdater app not found at {APP_PATH}", file=sys.stderr)
        return 1
    subprocess.Popen(["xdg-open", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    print("Opened ProjectUpdater with a Command Center update.")
    print(url)
    return 0


def add_common_project_args(parser: argparse.ArgumentParser, *, include_name: bool = True) -> None:
    if include_name:
        parser.add_argument("name", help="project name")
    parser.add_argument("--area", help="project area/category")
    parser.add_argument("--goal", action="append", help="project goal; repeat for multiple goals")
    parser.add_argument("--next-action", dest="nextAction", help="next small action")
    parser.add_argument("--path", dest="referencePath", help="project folder/reference path")
    parser.add_argument("--priority", choices=sorted(PRIORITIES), help="priority")
    parser.add_argument("--status", choices=sorted(STATUSES), help="status")
    parser.add_argument("--progress", type=int, help="progress percent, 0-100")
    parser.add_argument("--due-date", dest="dueDate", help="due date as YYYY-MM-DD")
    parser.add_argument("--reminder-days", dest="reminderDays", type=int, help="stale reminder window in days")
    parser.add_argument("--note", help="note text to attach while applying the project command")
    parser.add_argument("--note-type", dest="noteType", choices=sorted(NOTE_TYPES), default=None, help="note type")


def project_payload(args: argparse.Namespace) -> dict:
    return {
        "name": getattr(args, "name", None),
        "project": getattr(args, "project", None),
        "area": args.area,
        "goals": args.goal,
        "nextAction": args.nextAction,
        "referencePath": args.referencePath,
        "priority": args.priority,
        "status": args.status,
        "progress": args.progress,
        "dueDate": args.dueDate,
        "reminderDays": args.reminderDays,
        "note": args.note,
        "noteType": args.noteType,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url-only", action="store_true", help="print the command URL instead of opening it")
    parser.add_argument(
        "--target",
        choices=["auto", "command-center", "standalone"],
        default="auto",
        help="where to open ProjectUpdater; auto prefers the Command Center modal/same-origin app",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    new_parser = sub.add_parser("new", help="create or upsert a ProjectUpdater project")
    add_common_project_args(new_parser)

    update_parser = sub.add_parser("update", help="update an existing ProjectUpdater project")
    update_parser.add_argument("project", help="existing project name")
    add_common_project_args(update_parser, include_name=False)
    update_parser.add_argument("--rename", dest="name", help="rename the project")
    update_parser.add_argument(
        "--no-visit",
        dest="markVisited",
        action="store_false",
        default=True,
        help="do not reset the project's last-visited timestamp",
    )

    note_parser = sub.add_parser("note", help="add a ProjectUpdater note")
    note_parser.add_argument("project", help="existing project name")
    note_parser.add_argument("text", help="note text")
    note_parser.add_argument("--type", dest="noteType", choices=sorted(NOTE_TYPES), default="Note", help="note type")
    note_parser.add_argument("--energy", choices=["Low", "Medium", "High"], help="energy")
    note_parser.add_argument("--next-action", dest="nextAction", help="new next action")
    note_parser.add_argument("--status", choices=sorted(STATUSES), help="new status")
    note_parser.add_argument("--progress", type=int, help="new progress percent, 0-100")

    args = parser.parse_args()
    if args.command == "new":
        url = encode_command("new_project", project_payload(args), target=args.target)
    elif args.command == "update":
        payload = project_payload(args)
        payload["markVisited"] = args.markVisited
        url = encode_command("update_project", payload, target=args.target)
    elif args.command == "note":
        url = encode_command("add_note", {
            "project": args.project,
            "text": args.text,
            "noteType": args.noteType,
            "energy": args.energy,
            "nextAction": args.nextAction,
            "status": args.status,
            "progress": args.progress,
        }, target=args.target)
    else:
        parser.error(f"unknown command {args.command}")
    return maybe_open(url, url_only=args.url_only)


if __name__ == "__main__":
    raise SystemExit(main())
