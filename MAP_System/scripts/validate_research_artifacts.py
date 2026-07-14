#!/usr/bin/env python3
"""Validate MAP Research System templates and completed research artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TEMPLATES: dict[str, list[str]] = {
    "RESEARCH_BRIEF_TEMPLATE.md": [
        "# Research Brief",
        "Brief ID:",
        "## Research question",
        "## Why this matters",
        "## What would count as an answer",
        "## Time sensitivity",
        "## Linked artifacts",
    ],
    "SOURCE_MAP_TEMPLATE.md": [
        "# Source Map",
        "Source Map ID:",
        "## Candidate sources",
        "## Coverage check",
    ],
    "SOURCE_EVALUATION_TEMPLATE.md": [
        "# Source Evaluation",
        "Evaluation ID:",
        "## Ratings",
        "## Flags",
        "## Low-confidence claims",
        "## Contradictions",
    ],
    "CLAIM_EVIDENCE_MATRIX_TEMPLATE.md": [
        "# Claim Evidence Matrix",
        "Matrix ID:",
        "## Claims",
        "## Unsourced claims used downstream",
    ],
    "ASSUMPTION_REGISTER_TEMPLATE.md": [
        "# Assumption Register",
        "Register ID:",
        "## Assumptions",
        "## Gating rule",
    ],
    "RESEARCH_SUMMARY_TEMPLATE.md": [
        "# Research Summary",
        "Summary ID:",
        "## Question",
        "## Answer",
        "## Confidence",
        "## Confidence decays after",
        "## Open questions",
        "## Downstream effect",
    ],
}

ARTIFACT_REQUIREMENTS: dict[str, list[str]] = {
    "BRIEF": REQUIRED_TEMPLATES["RESEARCH_BRIEF_TEMPLATE.md"],
    "SOURCE-MAP": REQUIRED_TEMPLATES["SOURCE_MAP_TEMPLATE.md"],
    "SOURCE-EVAL": REQUIRED_TEMPLATES["SOURCE_EVALUATION_TEMPLATE.md"],
    "CLAIM-MATRIX": REQUIRED_TEMPLATES["CLAIM_EVIDENCE_MATRIX_TEMPLATE.md"],
    "ASSUMPTIONS": REQUIRED_TEMPLATES["ASSUMPTION_REGISTER_TEMPLATE.md"],
    "SUMMARY": REQUIRED_TEMPLATES["RESEARCH_SUMMARY_TEMPLATE.md"],
}

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


def check_templates(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    template_dir = root / "templates" / "research"
    for name, fragments in REQUIRED_TEMPLATES.items():
        path = template_dir / name
        if not path.exists():
            issues.append(Issue(path, "MISSING_TEMPLATE", "required Research System template is absent"))
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


def iter_research_artifacts(root: Path) -> list[Path]:
    candidates: list[Path] = []
    map_research = root / "artifacts" / "research"
    if map_research.exists():
        candidates.extend(path for path in map_research.rglob("*.md") if path.name != "README.md")

    projects_dir = root.parent / "Projects"
    if projects_dir.exists():
        for research_dir in projects_dir.glob("*/research"):
            candidates.extend(path for path in research_dir.rglob("*.md") if path.name != "README.md")

    return sorted(set(candidates))


def check_artifact(path: Path) -> list[Issue]:
    issues: list[Issue] = []
    kind = artifact_kind(path)
    if kind is None:
        return [Issue(path, "UNKNOWN_RESEARCH_ARTIFACT", "filename must start with a known research artifact prefix")]

    text = read_text(path)
    if not text.strip():
        return [Issue(path, "EMPTY_ARTIFACT", "research artifact has no content")]

    issues.extend(check_required_fragments(path, text, ARTIFACT_REQUIREMENTS[kind]))

    if FINAL_STATUS_RE.search(text):
        placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
        if placeholders:
            issues.append(
                Issue(
                    path,
                    "FINAL_PLACEHOLDER",
                    "final/submitted artifact still contains placeholders: " + ", ".join(placeholders[:5]),
                )
            )

    return issues


def check_artifacts(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    for path in iter_research_artifacts(root):
        issues.extend(check_artifact(path))
    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="MAP_System root to validate")
    parser.add_argument(
        "--templates-only",
        action="store_true",
        help="Only validate Research System template files",
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
        print(f"FAIL research validation: {len(issues)} issue(s)")
        return 1

    print("PASS research validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
