#!/usr/bin/env python3
"""Validate MAP Context Packet template and packet artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TEMPLATE: list[str] = [
    "# Context Packet",
    "Packet ID:",
    "Anchor:",
    "Assembled by:",
    "Date:",
    "## Required",
    "## Optional (trigger-gated)",
    "## Excluded",
    "## Staleness check",
    "## Notes",
]

PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
FINAL_STATUS_RE = re.compile(r"^Status:\s*(FINAL|SUBMITTED|COMPLETE|COMPLETED)\s*$", re.MULTILINE | re.IGNORECASE)


@dataclass(frozen=True)
class Issue:
    path: Path
    code: str
    detail: str

    def format(self, root: Path) -> str:
        try:
            rel = self.path.relative_to(root)
        except ValueError:
            rel = self.path
        return f"ERROR {rel}: {self.code}: {self.detail}"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def check_required_fragments(path: Path, text: str, fragments: list[str]) -> list[Issue]:
    issues: list[Issue] = []
    for fragment in fragments:
        if fragment not in text:
            issues.append(Issue(path, "MISSING_FRAGMENT", fragment))
    return issues


def check_template(root: Path) -> list[Issue]:
    path = root / "templates" / "CONTEXT_PACKET_TEMPLATE.md"
    if not path.exists():
        return [Issue(path, "MISSING_TEMPLATE", "required Context Packet template is absent")]

    text = read_text(path)
    if not text.strip():
        return [Issue(path, "EMPTY_TEMPLATE", "template has no content")]

    return check_required_fragments(path, text, REQUIRED_TEMPLATE)


def is_context_packet(path: Path) -> bool:
    return path.stem.upper().startswith("CONTEXT")


def iter_context_packets(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for packet_dir in [
        root / "context",
        root / "contexts",
        root / "context-packets",
        root / "artifacts" / "context",
        root / "artifacts" / "contexts",
        root / "artifacts" / "context-packets",
    ]:
        if packet_dir.exists():
            candidates.extend(path for path in packet_dir.rglob("*.md") if path.name != "README.md")

    projects_dir = root.parent / "Projects"
    if projects_dir.exists():
        for project_dir in projects_dir.iterdir():
            if not project_dir.is_dir():
                continue
            for name in ["context", "contexts", "context-packets"]:
                packet_dir = project_dir / name
                if packet_dir.exists():
                    candidates.extend(path for path in packet_dir.rglob("*.md") if path.name != "README.md")

    return sorted(set(candidates))


def check_packet(path: Path) -> list[Issue]:
    if not is_context_packet(path):
        return [Issue(path, "UNKNOWN_CONTEXT_PACKET", "filename must start with CONTEXT")]

    text = read_text(path)
    if not text.strip():
        return [Issue(path, "EMPTY_PACKET", "context packet has no content")]

    issues = check_required_fragments(path, text, REQUIRED_TEMPLATE)
    if FINAL_STATUS_RE.search(text):
        placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
        if placeholders:
            issues.append(
                Issue(
                    path,
                    "FINAL_PLACEHOLDER",
                    "final/submitted context packet still contains placeholders: "
                    + ", ".join(placeholders[:5]),
                )
            )

    return issues


def check_packets(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    for path in iter_context_packets(root):
        issues.extend(check_packet(path))
    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="MAP_System root to validate")
    parser.add_argument(
        "--templates-only",
        action="store_true",
        help="Only validate Context Packet template file",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    issues = check_template(root)
    if not args.templates_only:
        issues.extend(check_packets(root))

    if issues:
        for issue in issues:
            print(issue.format(root))
        print(f"FAIL context packet validation: {len(issues)} issue(s)")
        return 1

    print("PASS context packet validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
