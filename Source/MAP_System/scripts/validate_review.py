#!/usr/bin/env python3
"""Validate a review record before a task can be APPROVED.

HPOM-004: No task can become APPROVED without a review record.
The review record must cover acceptance criteria, forbidden changes,
files reviewed, and identify risks.

Usage:
    python3 MAP_System/scripts/validate_review.py \\
        --review-record <path> \\
        [--task-id TASK-NNN]

Exit codes:
    0  review record is valid
    1  review record is missing required sections or has invalid verdict
    2  usage error
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REQUIRED_SECTIONS = [
    "verdict",
    "acceptance criteria",
    "files reviewed",
    "forbidden changes",
]

VALID_VERDICTS = {"APPROVED", "CHANGES_REQUESTED", "BLOCKED"}

VERDICT_RE = re.compile(
    r"(APPROVED|CHANGES_REQUESTED|BLOCKED)",
    re.IGNORECASE,
)

SECTION_HEADERS = re.compile(r"^##\s+(.+)$", re.MULTILINE)

TASK_ID_RE = re.compile(r"task_id\s*:\s*(TASK-\w+)", re.IGNORECASE)
REVIEWER_RE = re.compile(r"reviewer\s*:\s*(\S+)", re.IGNORECASE)
TASK_OWNER_RE = re.compile(r"task_owner\s*:\s*(\S+)", re.IGNORECASE)


def normalize(text: str) -> str:
    return text.lower().strip()


def find_sections(text: str) -> dict[str, str]:
    """Return a mapping of normalized section name → section body."""
    sections: dict[str, str] = {}
    headers = list(SECTION_HEADERS.finditer(text))
    for i, match in enumerate(headers):
        name = normalize(match.group(1))
        start = match.end()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        sections[name] = text[start:end].strip()
    return sections


def check_self_review(text: str) -> str | None:
    """Return an error string if reviewer == task_owner, else None."""
    id_match = REVIEWER_RE.search(text[:500])
    owner_match = TASK_OWNER_RE.search(text[:500])
    if id_match and owner_match:
        reviewer = id_match.group(1).strip().lower()
        owner = owner_match.group(1).strip().lower()
        if reviewer == owner or reviewer in owner or owner in reviewer:
            return f"SELF_REVIEW: reviewer '{reviewer}' matches task_owner '{owner}'"
    return None


def check_verdict(sections: dict[str, str]) -> list[str]:
    issues = []
    body = sections.get("verdict", "")
    if not body:
        issues.append("MISSING_SECTION: ## Verdict")
        return issues
    match = VERDICT_RE.search(body)
    if not match:
        issues.append(f"INVALID_VERDICT: no valid verdict in Verdict section (expected one of {sorted(VALID_VERDICTS)})")
    else:
        verdict = match.group(1).upper()
        if verdict in ("CHANGES_REQUESTED", "BLOCKED"):
            issues.append(f"VERDICT_{verdict}: task cannot be APPROVED with this verdict")
    return issues


def check_criteria(sections: dict[str, str]) -> list[str]:
    issues = []
    body = sections.get("acceptance criteria check", "") or sections.get("acceptance criteria", "")
    if not body:
        issues.append("MISSING_SECTION: ## Acceptance Criteria Check")
        return issues
    # Must have at least one table row with PASS/FAIL or a substantive entry
    has_row = bool(re.search(r"\|\s*\d+\s*\|", body) or re.search(r"PASS|FAIL|PARTIAL", body, re.IGNORECASE))
    if not has_row:
        issues.append("EMPTY_CRITERIA: Acceptance Criteria section has no checked rows (need PASS/FAIL/PARTIAL entries)")
    return issues


def check_files_reviewed(sections: dict[str, str]) -> list[str]:
    issues = []
    body = sections.get("files reviewed", "")
    if not body:
        issues.append("MISSING_SECTION: ## Files Reviewed")
        return issues
    has_file = bool(re.search(r"`[^`]+`|\S+\.\w+", body))
    if not has_file:
        issues.append("EMPTY_FILES: Files Reviewed section lists no files")
    return issues


def check_forbidden(sections: dict[str, str]) -> list[str]:
    issues = []
    body = sections.get("forbidden changes check", "") or sections.get("forbidden changes", "")
    if not body:
        issues.append("MISSING_SECTION: ## Forbidden Changes Check")
    return issues


def validate(text: str, task_id: str | None = None) -> list[str]:
    issues: list[str] = []

    # Self-review check
    self_review = check_self_review(text)
    if self_review:
        issues.append(self_review)

    # Task ID match (if provided)
    if task_id:
        id_match = TASK_ID_RE.search(text[:500])
        if id_match:
            found_id = id_match.group(1).strip()
            if found_id.upper() != task_id.upper():
                issues.append(f"TASK_ID_MISMATCH: review record says '{found_id}', expected '{task_id}'")

    sections = find_sections(text)

    issues.extend(check_verdict(sections))
    issues.extend(check_criteria(sections))
    issues.extend(check_files_reviewed(sections))
    issues.extend(check_forbidden(sections))

    return issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review-record", required=True, help="Path to the review record file")
    parser.add_argument("--task-id", help="Expected task ID (optional; cross-checks header)")
    args = parser.parse_args(argv)

    path = Path(args.review_record)
    if not path.exists():
        print(f"error: review record not found: {path}", file=sys.stderr)
        return 2

    text = path.read_text(encoding="utf-8", errors="replace")
    issues = validate(text, task_id=args.task_id)

    if issues:
        for issue in issues:
            print(f"FAIL {issue}", file=sys.stderr)
        print(f"\n{len(issues)} issue(s) found. Task cannot be APPROVED.", file=sys.stderr)
        return 1

    print(f"OK  review record valid: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
