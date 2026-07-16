#!/usr/bin/env python3
"""Coordinate repository-global Git operations with a small MAP lock file."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / ".locks" / "git-operation.json"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_lock(path: Path) -> dict | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def acquire(args: argparse.Namespace) -> int:
    existing = read_lock(args.lock_file)
    if existing and not args.force:
        print(json.dumps({"acquired": False, "existing": existing}, indent=2))
        return 1
    payload = {
        "owner": args.owner,
        "repo": str(args.repo.resolve()),
        "operation": args.operation,
        "stop_condition": args.stop_condition,
        "created_at": now(),
    }
    args.lock_file.parent.mkdir(parents=True, exist_ok=True)
    args.lock_file.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"acquired": True, "lock": payload}, indent=2))
    return 0


def release(args: argparse.Namespace) -> int:
    existing = read_lock(args.lock_file)
    if not existing:
        print(json.dumps({"released": False, "reason": "no_lock"}))
        return 1
    if existing.get("owner") != args.owner and not args.force:
        print(json.dumps({"released": False, "reason": "owner_mismatch", "existing": existing}, indent=2))
        return 1
    args.lock_file.unlink()
    print(json.dumps({"released": True, "previous": existing}, indent=2))
    return 0


def status(args: argparse.Namespace) -> int:
    existing = read_lock(args.lock_file)
    print(json.dumps({"locked": existing is not None, "lock": existing}, indent=2))
    return 0 if existing is None else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock-file", type=Path, default=DEFAULT_LOCK)
    sub = parser.add_subparsers(dest="command", required=True)

    acquire_cmd = sub.add_parser("acquire")
    acquire_cmd.add_argument("--owner", required=True)
    acquire_cmd.add_argument("--operation", required=True)
    acquire_cmd.add_argument("--repo", type=Path, default=ROOT.parent)
    acquire_cmd.add_argument("--stop-condition", required=True)
    acquire_cmd.add_argument("--force", action="store_true")
    acquire_cmd.set_defaults(func=acquire)

    release_cmd = sub.add_parser("release")
    release_cmd.add_argument("--owner", required=True)
    release_cmd.add_argument("--force", action="store_true")
    release_cmd.set_defaults(func=release)

    status_cmd = sub.add_parser("status")
    status_cmd.set_defaults(func=status)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
