#!/usr/bin/env python3
"""Validate MAP Self-Repair templates and repair artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TEMPLATES: dict[str, list[str]] = {
    "REPAIR_RECORD_TEMPLATE.md": [
        "# Repair Record",
        "Repair ID:",
        "Severity:",
        "Status:",
        "## What was found",
        "## Surfaced by",
        "## Severity rationale",
        "## Proposed or applied fix",
        "## Authority check",
        "## Verification",
        "## Recurrence check",
    ],
    "HEALTH_CHECK_REPORT_TEMPLATE.md": [
        "# Health Check Report",
        "Health ID:",
        "Status:",
        "## Checks run",
        "## Findings requiring a Repair Record",
        "## Overall assessment",
    ],
}

ARTIFACT_REQUIREMENTS: dict[str, list[str]] = {
    "REPAIR": REQUIRED_TEMPLATES["REPAIR_RECORD_TEMPLATE.md"],
    "HEALTH": REQUIRED_TEMPLATES["HEALTH_CHECK_REPORT_TEMPLATE.md"],
}

PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
FINAL_STATUS_RE = re.compile(
    r"^Status:\s*(APPLIED|APPROVED|CLEAN|FINDINGS_FILED|COMPLETE|COMPLETED|FINAL)\s*$",
    re.MULTILINE | re.IGNORECASE,
)


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


def check_templates(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    template_dir = root / "templates" / "repairs"
    for name, fragments in REQUIRED_TEMPLATES.items():
        path = template_dir / name
        if not path.exists():
            issues.append(Issue(path, "MISSING_TEMPLATE", "required Self-Repair template is absent"))
            continue
        text = read_text(path)
        if not text.strip():
            issues.append(Issue(path, "EMPTY_TEMPLATE", "template has no content"))
            continue
        issues.extend(check_required_fragments(path, text, fragments))
    return issues


def artifact_kind(path: Path) -> str | None:
    stem = path.stem.upper()
    for kind in sorted(ARTIFACT_REQUIREMENTS, key=len, reverse=True):
        if stem.startswith(kind):
            return kind
    return None


def iter_repair_artifacts(root: Path) -> list[Path]:
    candidates: list[Path] = []
    map_repairs = root / "repairs"
    if map_repairs.exists():
        candidates.extend(path for path in map_repairs.rglob("*.md") if path.name != "README.md")

    projects_dir = root.parent / "Projects"
    if projects_dir.exists():
        for repair_dir in projects_dir.glob("*/repairs"):
            candidates.extend(path for path in repair_dir.rglob("*.md") if path.name != "README.md")
        for health_dir in projects_dir.glob("*/health"):
            candidates.extend(path for path in health_dir.rglob("*.md") if path.name != "README.md")

    return sorted(set(candidates))


def check_artifact(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    kind = artifact_kind(path)
    if kind is None:
        return [Issue(path, "UNKNOWN_REPAIR_ARTIFACT", "filename must start with REPAIR or HEALTH")]

    text = read_text(path)
    if not text.strip():
        return [Issue(path, "EMPTY_ARTIFACT", "repair artifact has no content")]

    issues.extend(check_required_fragments(path, text, ARTIFACT_REQUIREMENTS[kind]))

    if FINAL_STATUS_RE.search(text):
        placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
        if placeholders:
            issues.append(
                Issue(
                    path,
                    "FINAL_PLACEHOLDER",
                    "final/applied health or repair artifact still contains placeholders: "
                    + ", ".join(placeholders[:5]),
                )
            )

    return issues


def check_artifacts(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    for path in iter_repair_artifacts(root):
        issues.extend(check_artifact(path))
    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="MAP_System root to validate")
    parser.add_argument(
        "--templates-only",
        action="store_true",
        help="Only validate Self-Repair template files",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    issues = check_templates(root)
    if not args.templates_only:
        issues.extend(check_artifacts(root))

    if issues:
        for issue in issues:
            print(issue.format(root))
        print(f"FAIL repair validation: {len(issues)} issue(s)")
        return 1

    print("PASS repair validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
