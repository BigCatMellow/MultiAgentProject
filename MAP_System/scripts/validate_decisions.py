#!/usr/bin/env python3
"""Validate decision records in shared/decisions.md against required HPOM schema.

HPOM-009: Major decisions must have a durable record with required fields.
Entries missing required fields are flagged; superseded entries are noted.

Usage:
    python3 MAP_System/scripts/validate_decisions.py [--decisions-file PATH] [--emit-index]

Exit codes:
    0  all entries valid (or no entries found)
    1  one or more entries missing required fields
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DECISIONS = ROOT / "shared" / "decisions.md"
DEFAULT_INDEX_OUT = ROOT / "shared" / "DECISIONS.md"

REQUIRED_FIELDS = {"id", "owner", "reason", "applies_to", "date", "status"}

# Matches ## DEC-NNN: Title headers
DEC_HEADER = re.compile(r"^##\s+(DEC-\d+):\s+(.+)$", re.MULTILINE)

# Field extractors — look for "field: value" lines (case-insensitive) within a block
FIELD_PATTERNS = {
    "owner": re.compile(r"^\*?\*?owner\*?\*?\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "date": re.compile(r"^\*?\*?(?:date|issued|recorded)\*?\*?\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "status": re.compile(r"^\*?\*?status\*?\*?\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "reason": re.compile(r"^\*?\*?(?:reason|why|context)\*?\*?\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "applies_to": re.compile(r"^\*?\*?applies.to\*?\*?\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "supersedes": re.compile(r"^\*?\*?supersedes\*?\*?\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    "superseded_by": re.compile(r"^\*?\*?superseded.by\*?\*?\s*:\s*(.+)$", re.IGNORECASE | re.MULTILINE),
}

DEC_REF = re.compile(r"\bDEC-\d+\b", re.IGNORECASE)
SUBJECT_STOPWORDS = {
    "across",
    "active",
    "agent",
    "agents",
    "all",
    "and",
    "architecture",
    "authority",
    "class",
    "code",
    "control",
    "current",
    "decision",
    "decisions",
    "framework",
    "layer",
    "map",
    "policy",
    "project",
    "projects",
    "scope",
    "system",
    "task",
    "tasks",
    "the",
    "use",
}


def extract_blocks(text: str) -> list[dict]:
    """Split decisions.md into per-DEC blocks and parse fields."""
    matches = list(DEC_HEADER.finditer(text))
    blocks = []
    for i, match in enumerate(matches):
        dec_id = match.group(1)
        title = match.group(2).strip()
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block_text = text[start:end]

        fields: dict[str, str] = {"id": dec_id, "title": title}
        for field, pattern in FIELD_PATTERNS.items():
            m = pattern.search(block_text)
            if m:
                fields[field] = m.group(1).strip()

        # Heuristic: if block body exists, treat presence as reason
        body = block_text[len(match.group(0)):].strip()
        if body and "reason" not in fields:
            # Treat the first non-empty paragraph as the reason
            first_para = body.split("\n\n")[0].strip().lstrip("#").strip()
            if first_para:
                fields["reason"] = first_para[:120]

        # Infer date from common patterns in block text
        if "date" not in fields:
            date_match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", block_text)
            if date_match:
                fields["date"] = date_match.group(1)

        # Infer applies_to from "applies to" prose
        if "applies_to" not in fields:
            at_match = re.search(r"applies? to[:\s]+(.+?)[\.\n]", block_text, re.IGNORECASE)
            if at_match:
                fields["applies_to"] = at_match.group(1).strip()[:80]

        fields["_raw"] = block_text

        blocks.append(fields)
    return blocks


def check_block(block: dict) -> list[str]:
    issues = []
    for field in REQUIRED_FIELDS:
        if field not in block or not block[field].strip():
            issues.append(f"MISSING_FIELD: {field}")
    status = block.get("status", "").lower()
    if status.startswith("superseded"):
        sup_by = block.get("superseded_by", "")
        # Try to extract the superseding decision from the status text itself
        sup_ref = sup_by or re.search(r"(DEC-\d+)", block.get("status", ""), re.IGNORECASE)
        sup_ref = sup_ref.group(0) if hasattr(sup_ref, "group") else sup_ref or "(unspecified)"
        issues.append(f"SUPERSEDED: superseded_by={sup_ref}")
    return issues


def decision_refs(value: str | None) -> set[str]:
    """Return normalized DEC-NNN references from a link-like field."""
    if not value:
        return set()
    return {match.group(0).upper() for match in DEC_REF.finditer(value)}


def supersedes_refs(block: dict) -> set[str]:
    return decision_refs(block.get("supersedes"))


def superseded_by_refs(block: dict) -> set[str]:
    refs = decision_refs(block.get("superseded_by"))
    status = block.get("status", "")
    if re.search(r"\bsuperseded\s+by\b", status, re.IGNORECASE):
        refs.update(decision_refs(status))
    return refs


def subject_terms(block: dict) -> set[str]:
    """Extract conservative subject tokens from Applies-To for pair reporting."""
    subject = block.get("applies_to", "")
    tokens = re.findall(r"[a-z0-9]+", subject.lower())
    return {token for token in tokens if len(token) >= 4 and token not in SUBJECT_STOPWORDS}


def directly_superseded(block_a: dict, block_b: dict) -> bool:
    a_id = block_a["id"].upper()
    b_id = block_b["id"].upper()
    return (
        b_id in supersedes_refs(block_a)
        or b_id in superseded_by_refs(block_a)
        or a_id in supersedes_refs(block_b)
        or a_id in superseded_by_refs(block_b)
    )


def check_decision_conflicts(blocks: list[dict]) -> list[str]:
    """Report-only supersession and same-subject findings.

    This deliberately returns NOTE-level strings; it must not affect the
    validator's exit status until MAP has reviewed real-world noise.
    """
    issues: list[str] = []
    by_id = {block["id"].upper(): block for block in blocks}

    for block in blocks:
        dec_id = block["id"].upper()
        for target in sorted(supersedes_refs(block)):
            target_block = by_id.get(target)
            if target_block is None:
                issues.append(f"SUPERSESSION_DANGLING: {dec_id} supersedes unknown {target}")
            elif dec_id not in superseded_by_refs(target_block):
                issues.append(f"SUPERSESSION_ONE_WAY: {dec_id} supersedes {target}, but {target} does not list superseded_by {dec_id}")
        for target in sorted(superseded_by_refs(block)):
            target_block = by_id.get(target)
            if target_block is None:
                issues.append(f"SUPERSESSION_DANGLING: {dec_id} superseded_by unknown {target}")
            elif dec_id not in supersedes_refs(target_block):
                issues.append(f"SUPERSESSION_ONE_WAY: {dec_id} superseded_by {target}, but {target} does not list supersedes {dec_id}")

    for index, block_a in enumerate(blocks):
        for block_b in blocks[index + 1:]:
            if directly_superseded(block_a, block_b):
                continue
            shared = subject_terms(block_a) & subject_terms(block_b)
            if len(shared) >= 2:
                issues.append(
                    "POSSIBLE_DECISION_CONFLICT: "
                    f"{block_a['id']} and {block_b['id']} share subject terms "
                    f"{', '.join(sorted(shared))} without supersession links"
                )

    return issues


def emit_index(blocks: list[dict], out_path: Path) -> None:
    """Write a machine-readable DECISIONS.md index of active decisions."""
    from datetime import date as _date
    today = _date.today().isoformat()
    lines = [
        "<!-- hpom: file: shared/DECISIONS.md -->",
        "<!-- hpom: project: MAP -->",
        "<!-- hpom: state_owner: command-center -->",
        "<!-- hpom: status: CURRENT -->",
        f"<!-- hpom: last_verified: {today} -->",
        "<!-- hpom: verified_against: validate_decisions.py auto-generated -->",
        "<!-- hpom: confidence: HIGH -->",
        "<!-- hpom: supersedes: NONE -->",
        "<!-- hpom: superseded_by: NONE -->",
        "",
        "# DECISIONS Index",
        "",
        "Auto-generated by validate_decisions.py. Do not edit manually.",
        "Source: shared/decisions.md",
        "",
        "| ID | Title | Status | Owner | Date |",
        "|---|---|---|---|---|",
    ]
    for b in blocks:
        status = b.get("status", "unknown")
        if status.lower().startswith("superseded"):
            continue  # skip superseded in active index
        lines.append(
            f"| {b['id']} | {b.get('title','')} | {status} | {b.get('owner','?')} | {b.get('date','?')} |"
        )
    lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Index written to {out_path}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--decisions-file",
        default=str(DEFAULT_DECISIONS),
        help="Path to decisions.md (default: MAP_System/shared/decisions.md)",
    )
    parser.add_argument(
        "--emit-index",
        action="store_true",
        help="Write MAP_System/shared/DECISIONS.md active-decisions index",
    )
    args = parser.parse_args(argv)

    decisions_file = Path(args.decisions_file)
    if not decisions_file.exists():
        print(f"ERROR: decisions file not found: {decisions_file}", file=sys.stderr)
        return 1

    text = decisions_file.read_text(encoding="utf-8", errors="replace")
    blocks = extract_blocks(text)

    if not blocks:
        print("No DEC-NNN entries found.")
        return 0

    failures = 0
    for block in blocks:
        issues = check_block(block)
        dec_id = block["id"]
        title = block.get("title", "")
        label = f"{dec_id}: {title}"
        if not issues:
            print(f"  OK   {label}")
        else:
            for issue in issues:
                is_hard = issue.startswith("MISSING")
                if is_hard:
                    failures += 1
                    print(f"  FAIL {label}: {issue}")
                else:
                    print(f"  NOTE {label}: {issue}")

    conflict_issues = check_decision_conflicts(blocks)
    for issue in conflict_issues:
        print(f"  NOTE decision-conflicts: {issue}")

    active = sum(1 for b in blocks if b.get("status", "").lower() not in ("superseded",))
    print(
        f"\n{len(blocks)} decision(s) checked. {active} active. "
        f"{failures} failure(s). {len(conflict_issues)} report-only conflict note(s)."
    )

    if args.emit_index:
        emit_index(blocks, DEFAULT_INDEX_OUT)

    return 1 if failures > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
