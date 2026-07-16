#!/usr/bin/env python3
"""Fail when primary operating docs reintroduce the legacy repo path."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEGACY_PATH = "/home/home/Downloads/MultiAgentProject"
CANONICAL_PATH = "/home/home/Projects/MultiAgentProject"

PRIMARY_DOCS = [
    ROOT / "AGENTS.md",
    ROOT / "docs" / "agent-quickstart.md",
    ROOT / "docs" / "project-map.md",
    ROOT / "MAP_System" / "AGENTS.md",
    ROOT / "MAP_System" / "notes" / "git-setup.md",
    ROOT / "MAP_System" / "notes" / "command-center-lab-restart-startup.md",
    ROOT / "MAP_System" / "notes" / "command-center-later.md",
    ROOT / "MAP_System" / "scripts" / "ai-command-center-cli",
    ROOT / "MAP_System" / "scripts" / "ai-command-center-shell",
    ROOT / "MAP_System" / "scripts" / "ai-command-center-antigravity",
    ROOT / "MAP_System" / "scripts" / "agent-deck",
]

MUST_NAME_CANONICAL = [
    ROOT / "MAP_System" / "AGENTS.md",
    ROOT / "MAP_System" / "notes" / "git-setup.md",
    ROOT / "MAP_System" / "notes" / "command-center-lab-restart-startup.md",
    ROOT / "MAP_System" / "scripts" / "ai-command-center-cli",
    ROOT / "MAP_System" / "scripts" / "ai-command-center-shell",
    ROOT / "MAP_System" / "scripts" / "ai-command-center-antigravity",
    ROOT / "MAP_System" / "scripts" / "agent-deck",
]


def main() -> int:
    errors: list[str] = []

    for path in PRIMARY_DOCS:
        text = path.read_text(encoding="utf-8")
        if LEGACY_PATH in text:
            rel = path.relative_to(ROOT)
            errors.append(f"{rel}: contains legacy repo path {LEGACY_PATH}")

    for path in MUST_NAME_CANONICAL:
        text = path.read_text(encoding="utf-8")
        if CANONICAL_PATH not in text:
            rel = path.relative_to(ROOT)
            errors.append(f"{rel}: missing canonical repo path {CANONICAL_PATH}")

    if errors:
        for error in errors:
            print(f"ERROR {error}")
        return 1

    print("PASS canonical repo paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
