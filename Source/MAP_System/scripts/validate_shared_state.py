#!/usr/bin/env python3
"""Validate shared-state files have required HPOM metadata headers.

HPOM-007: Shared files without metadata are flagged. STALE or SUPERSEDED
files are reported so agents do not use stale authority.

Usage:
    python3 MAP_System/scripts/validate_shared_state.py [--shared-dir PATH] [--strict]

Exit codes:
    0  all files valid
    1  one or more files missing metadata or flagged STALE/SUPERSEDED
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SHARED = ROOT / "shared"

REQUIRED_FIELDS = [
    "file",
    "project",
    "state_owner",
    "status",
    "last_verified",
    "verified_against",
    "confidence",
    "supersedes",
    "superseded_by",
]

WARN_STATUSES = {"STALE", "SUPERSEDED", "NEEDS_REVIEW"}


def parse_metadata(text: str) -> dict[str, str]:
    """Extract <!-- hpom: key: value --> comment metadata from file header."""
    meta: dict[str, str] = {}
    pattern = re.compile(r"<!--\s*hpom\s*:\s*(\w+)\s*:\s*(.+?)\s*-->", re.IGNORECASE)
    for match in pattern.finditer(text[:2000]):  # only scan file header
        meta[match.group(1).lower()] = match.group(2).strip()
    return meta


def check_file(path: Path) -> list[str]:
    """Return list of issue strings for a shared file. Empty = clean."""
    issues: list[str] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [f"UNREADABLE: {exc}"]

    meta = parse_metadata(text)

    if not meta:
        issues.append("MISSING_METADATA: no <!-- hpom: ... --> fields found in header")
        return issues

    for field in REQUIRED_FIELDS:
        if field not in meta:
            issues.append(f"MISSING_FIELD: {field}")

    status = meta.get("status", "").upper()
    if status in WARN_STATUSES:
        superseded_by = meta.get("superseded_by", "")
        detail = f" (superseded_by: {superseded_by})" if superseded_by else ""
        issues.append(f"STATUS_{status}{detail}")

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--shared-dir",
        default=str(DEFAULT_SHARED),
        help="Path to shared/ directory (default: MAP_System/shared/)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 1 even for STALE/NEEDS_REVIEW (default: exit 1 only for MISSING_METADATA/MISSING_FIELD)",
    )
    args = parser.parse_args(argv)

    shared_dir = Path(args.shared_dir)
    if not shared_dir.is_dir():
        print(f"ERROR: shared dir not found: {shared_dir}", file=sys.stderr)
        return 1

    md_files = sorted(shared_dir.glob("*.md"))
    if not md_files:
        print(f"No .md files found in {shared_dir}")
        return 0

    total = 0
    hard_failures = 0
    warn_count = 0

    for path in md_files:
        issues = check_file(path)
        rel = path.relative_to(ROOT.parent) if ROOT.parent in path.parents else path
        if not issues:
            print(f"  OK   {rel}")
        else:
            for issue in issues:
                is_hard = issue.startswith("MISSING")
                is_warn = any(issue.startswith(f"STATUS_{s}") for s in WARN_STATUSES)
                if is_hard:
                    hard_failures += 1
                    print(f"  FAIL {rel}: {issue}")
                elif is_warn:
                    warn_count += 1
                    print(f"  WARN {rel}: {issue}")
                else:
                    print(f"  NOTE {rel}: {issue}")
        total += 1

    print(f"\n{total} file(s) checked. {hard_failures} failure(s). {warn_count} warning(s).")

    if hard_failures > 0:
        return 1
    if args.strict and warn_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
