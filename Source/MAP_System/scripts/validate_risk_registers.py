#!/usr/bin/env python3
"""Validate MAP Risk Register template and risk register artifacts."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_TEMPLATE: list[str] = [
    "# Risk Register Entry",
    "Risk ID:",
    "Project:",
    "Class:",
    "Severity:",
    "Owner:",
    "Date opened:",
    "Last reviewed:",
    "Status:",
    "## Description",
    "## Trigger / likelihood",
    "## Blast radius if realized",
    "## Current mitigation",
    "## Escalation",
    "## Acceptance (if Status: ACCEPTED)",
    "## Review history",
    "## Notes",
]

ALLOWED_CLASSES = {"SECURITY", "DATA", "PROCESS", "AVAILABILITY", "KNOWLEDGE"}
ALLOWED_SEVERITIES = {"COSMETIC", "DRIFT", "BLOCKING", "STRUCTURAL"}
ALLOWED_STATUSES = {"OPEN", "MITIGATED", "ACCEPTED", "CLOSED"}
PLACEHOLDER_RE = re.compile(r"<(?!!--)[^>\n]+>")


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
    path = root / "templates" / "RISK_REGISTER_TEMPLATE.md"
    if not path.exists():
        return [Issue(path, "MISSING_TEMPLATE", "required Risk Register template is absent")]

    text = read_text(path)
    if not text.strip():
        return [Issue(path, "EMPTY_TEMPLATE", "template has no content")]

    return check_required_fragments(path, text, REQUIRED_TEMPLATE)


def iter_risk_registers(root: Path) -> list[Path]:
    candidates: list[Path] = []
    for path in [
        root / "shared" / "RISK_REGISTER.md",
        root / "risks" / "RISK_REGISTER.md",
        root / "artifacts" / "risks" / "RISK_REGISTER.md",
    ]:
        if path.exists():
            candidates.append(path)

    projects_dir = root.parent / "Projects"
    if projects_dir.exists():
        for risk_dir in projects_dir.glob("*/risks"):
            candidates.extend(path for path in risk_dir.rglob("*.md") if path.name != "README.md")

    return sorted(set(candidates))


def field_value(text: str, field: str) -> str | None:
    match = re.search(rf"^{re.escape(field)}:\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else None


def check_enum(path: Path, text: str, field: str, allowed: set[str]) -> list[Issue]:
    value = field_value(text, field)
    if value is None:
        return []
    normalized = value.upper()
    if "/" in normalized:
        return [
            Issue(
                path,
                "UNRESOLVED_ENUM",
                f"{field} still contains template choices instead of one value: {value}",
            )
        ]
    if normalized not in allowed:
        return [
            Issue(
                path,
                "UNKNOWN_ENUM",
                f"{field} must be one of {', '.join(sorted(allowed))}; found {value}",
            )
        ]
    return []


def check_register(path: Path) -> list[Issue]:
    if path.name != "RISK_REGISTER.md":
        return [Issue(path, "UNKNOWN_RISK_REGISTER", "risk artifacts must be named RISK_REGISTER.md")]

    text = read_text(path)
    if not text.strip():
        return [Issue(path, "EMPTY_REGISTER", "risk register has no content")]

    issues = check_required_fragments(path, text, REQUIRED_TEMPLATE)
    issues.extend(check_enum(path, text, "Class", ALLOWED_CLASSES))
    issues.extend(check_enum(path, text, "Severity", ALLOWED_SEVERITIES))
    issues.extend(check_enum(path, text, "Status", ALLOWED_STATUSES))

    placeholders = sorted(set(PLACEHOLDER_RE.findall(text)))
    if placeholders:
        issues.append(
            Issue(
                path,
                "REGISTER_PLACEHOLDER",
                "risk register still contains placeholders: " + ", ".join(placeholders[:5]),
            )
        )

    return issues


def check_registers(root: Path) -> list[Issue]:
    issues: list[Issue] = []
    for path in iter_risk_registers(root):
        issues.extend(check_register(path))
    return issues


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="MAP_System root to validate")
    parser.add_argument(
        "--templates-only",
        action="store_true",
        help="Only validate Risk Register template file",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    root = args.root.resolve()
    issues = check_template(root)
    if not args.templates_only:
        issues.extend(check_registers(root))

    if issues:
        for issue in issues:
            print(issue.format(root))
        print(f"FAIL risk register validation: {len(issues)} issue(s)")
        return 1

    print("PASS risk register validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
