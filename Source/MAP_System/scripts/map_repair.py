#!/usr/bin/env python3
"""Create MAP repair records with atomic file-lock ID allocation."""

from __future__ import annotations

import argparse
import contextlib
from datetime import date
import fcntl
import re
import sys
from pathlib import Path

try:
    from MAP_System.scripts.redaction import guard as redaction_guard
except ModuleNotFoundError:  # direct script execution
    from redaction import guard as redaction_guard


ROOT = Path(__file__).resolve().parents[1]
REPAIRS_DIR = ROOT / "repairs"
LOCKS_DIR = ROOT / ".locks"
REPAIR_ID_RE = re.compile(r"^REPAIR-(\d{4})$")
REPAIR_FILE_RE = re.compile(r"^REPAIR-(\d{4})(?:-|$)")
SLUG_RE = re.compile(r"[^a-z0-9]+")


class RepairError(RuntimeError):
    pass


@contextlib.contextmanager
def repair_id_lock(root: Path):
    lock_dir = root / ".locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / "repair-REPAIR.lock"
    with lock_path.open("w", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def slugify(text: str) -> str:
    slug = SLUG_RE.sub("-", text.lower()).strip("-")
    return slug[:80].strip("-") or "repair"


def existing_repair_numbers(root: Path) -> list[int]:
    repair_dir = root / "repairs"
    if not repair_dir.exists():
        return []
    numbers = []
    for path in repair_dir.glob("REPAIR-*.md"):
        match = REPAIR_FILE_RE.match(path.name)
        if match:
            numbers.append(int(match.group(1)))
    return sorted(numbers)


def next_repair_id(root: Path) -> str:
    numbers = existing_repair_numbers(root)
    return f"REPAIR-{(numbers[-1] + 1) if numbers else 1:04d}"


def validate_repair_id(repair_id: str) -> str:
    repair_id = repair_id.upper()
    if not REPAIR_ID_RE.fullmatch(repair_id):
        raise RepairError("repair ID must look like REPAIR-0001 or use --repair-id auto")
    return repair_id


def render_repair_record(args: argparse.Namespace, repair_id: str) -> str:
    summary = args.summary.strip()
    surfaced_by = args.surfaced_by.strip()
    severity_rationale = args.severity_rationale.strip()
    fix = args.fix.strip()
    verification = args.verification.strip()
    recurrence = args.recurrence.strip()
    authority = args.authority.strip()
    return "\n".join([
        "# Repair Record",
        "",
        f"Repair ID: {repair_id}",
        f"Related task: {args.related_task}",
        f"Found by: {args.found_by}",
        f"Date: {args.date}",
        f"Severity: {args.severity}",
        f"Status: {args.status}",
        "",
        "## What was found",
        "",
        summary,
        "",
        "## Surfaced by",
        "",
        surfaced_by,
        "",
        "## Severity rationale",
        "",
        severity_rationale,
        "",
        "## Proposed or applied fix",
        "",
        fix,
        "",
        "## Authority check",
        "",
        authority,
        "",
        "## Verification",
        "",
        verification,
        "",
        "## Recurrence check",
        "",
        recurrence,
        "",
        "## Notes",
        "",
        args.notes.strip(),
        "",
    ])


def create_repair(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    repair_dir = root / "repairs"
    repair_dir.mkdir(parents=True, exist_ok=True)

    with repair_id_lock(root):
        repair_id = next_repair_id(root) if args.repair_id == "auto" else validate_repair_id(args.repair_id)
        filename = f"{repair_id}-{slugify(args.slug or args.summary)}.md"
        path = repair_dir / filename
        if path.exists():
            raise RepairError(f"repair record already exists: {path}")
        if any(existing.name.startswith(f"{repair_id}-") for existing in repair_dir.glob(f"{repair_id}*.md")):
            raise RepairError(f"repair ID already exists: {repair_id}")
        record = redaction_guard(render_repair_record(args, repair_id),
                                 f"repair create {repair_id}")
        path.write_text(record, encoding="utf-8")

    rel = path.relative_to(root.parent) if path.is_relative_to(root.parent) else path
    print(rel)
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="Create a repair record")
    create.add_argument("--repair-id", required=True, help="'auto' or explicit REPAIR-NNNN")
    create.add_argument("--slug", default="")
    create.add_argument("--related-task", default="NONE")
    create.add_argument("--found-by", required=True)
    create.add_argument("--date", default=date.today().isoformat())
    create.add_argument("--severity", choices=["COSMETIC", "DRIFT", "BLOCKING", "STRUCTURAL"], required=True)
    create.add_argument("--status", choices=["APPLIED", "PROPOSED", "APPROVED", "REJECTED"], default="PROPOSED")
    create.add_argument("--summary", required=True)
    create.add_argument("--surfaced-by", default="Manual observation.")
    create.add_argument("--severity-rationale", default="Severity classified per MAP_System/SELF_REPAIR_SYSTEM.md.")
    create.add_argument("--fix", default="TBD.")
    create.add_argument("--authority", default="- [ ] DRIFT or mechanical BLOCKING — core agent applied directly")
    create.add_argument("--verification", default="TBD.")
    create.add_argument("--recurrence", default="- [ ] First occurrence of this drift class")
    create.add_argument("--notes", default="-")
    create.set_defaults(func=create_repair)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return args.func(args)
    except RepairError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
