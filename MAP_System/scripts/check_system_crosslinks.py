#!/usr/bin/env python3
"""Report bidirectional Related-files links among MAP system documents."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "artifacts" / "audits" / "system-crosslink-bidirectionality-2026-07-03.md"

SYSTEM_DOCS = [
    "RESEARCH_SYSTEM.md",
    "SELF_REPAIR_SYSTEM.md",
    "CONTEXT_SYSTEM.md",
    "DECISION_AUTHORITY_SYSTEM.md",
    "HUMAN_INTERFACE_SYSTEM.md",
    "RISK_SYSTEM.md",
    "SECURITY_PERMISSIONS_SYSTEM.md",
    "CHANGE_CONTROL_SYSTEM.md",
    "PROJECT_BOOTSTRAPPING_SYSTEM.md",
    "ARCHIVE_RETENTION_SYSTEM.md",
    "RETROSPECTIVE_SYSTEM.md",
]

RELATED_HEADER_RE = re.compile(r"^##\s+Related files\s*$", re.IGNORECASE | re.MULTILINE)
NEXT_H2_RE = re.compile(r"^##\s+", re.MULTILINE)


@dataclass(frozen=True)
class LinkCheck:
    left: str
    right: str
    left_to_right: bool
    right_to_left: bool

    @property
    def status(self) -> str:
        if self.left_to_right and self.right_to_left:
            return "BIDIRECTIONAL"
        if self.left_to_right:
            return f"ONE_DIRECTIONAL: {self.left} -> {self.right}"
        if self.right_to_left:
            return f"ONE_DIRECTIONAL: {self.right} -> {self.left}"
        return "NO_RELATED_LINK"


def repo_path(path: Path) -> str:
    return str(path.relative_to(ROOT.parent))


def related_section(text: str, path: Path) -> str:
    match = RELATED_HEADER_RE.search(text)
    if not match:
        raise ValueError(f"missing Related files section: {repo_path(path)}")
    next_match = NEXT_H2_RE.search(text, match.end())
    end = next_match.start() if next_match else len(text)
    return text[match.end():end]


def load_related_links(root: Path) -> dict[str, set[str]]:
    links: dict[str, set[str]] = {}
    system_set = set(SYSTEM_DOCS)
    for doc in SYSTEM_DOCS:
        path = root / doc
        text = path.read_text(encoding="utf-8", errors="replace")
        section = related_section(text, path)
        refs = {candidate for candidate in system_set if candidate != doc and candidate in section}
        links[doc] = refs
    return links


def pair_checks(links: dict[str, set[str]]) -> list[LinkCheck]:
    checks: list[LinkCheck] = []
    for index, left in enumerate(SYSTEM_DOCS):
        for right in SYSTEM_DOCS[index + 1:]:
            checks.append(
                LinkCheck(
                    left=left,
                    right=right,
                    left_to_right=right in links[left],
                    right_to_left=left in links[right],
                )
            )
    return checks


def markdown_report(links: dict[str, set[str]], checks: list[LinkCheck], command: str) -> str:
    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    bidirectional = sum(1 for check in checks if check.status == "BIDIRECTIONAL")
    one_directional = sum(1 for check in checks if check.status.startswith("ONE_DIRECTIONAL"))
    no_link = sum(1 for check in checks if check.status == "NO_RELATED_LINK")
    directed_count = sum(len(refs) for refs in links.values())

    lines = [
        "# MAP System Cross-Link Bidirectionality Report",
        "",
        "task_id: TASK-131",
        "parent_task: TASK-129",
        f"generated_at: {generated_at}",
        "scope: findings-only; no `*_SYSTEM.md` files edited",
        "",
        "## Command",
        "",
        "```bash",
        command,
        "```",
        "",
        "## Systems Checked",
        "",
    ]
    lines.extend(f"- `MAP_System/{doc}`" for doc in SYSTEM_DOCS)
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- Systems checked: {len(SYSTEM_DOCS)}",
            f"- Unordered system pairs checked: {len(checks)}",
            f"- Directed Related-files links found among scoped systems: {directed_count}",
            f"- Bidirectional pairs: {bidirectional}",
            f"- One-directional gaps: {one_directional}",
            f"- Pairs with no scoped Related-files link: {no_link}",
            "",
            "## One-Directional Gaps",
            "",
        ]
    )

    gaps = [check for check in checks if check.status.startswith("ONE_DIRECTIONAL")]
    if gaps:
        lines.extend(["| Source | Target | Missing reverse |", "|---|---|---|"])
        for check in gaps:
            if check.left_to_right:
                source, target = check.left, check.right
            else:
                source, target = check.right, check.left
            lines.append(f"| `MAP_System/{source}` | `MAP_System/{target}` | `{target}` Related files does not list `{source}` |")
    else:
        lines.append("None.")

    lines.extend(
        [
            "",
            "## Pair Matrix",
            "",
            "| System A | System B | A -> B | B -> A | Status |",
            "|---|---|---:|---:|---|",
        ]
    )
    for check in checks:
        left_to_right = "yes" if check.left_to_right else "no"
        right_to_left = "yes" if check.right_to_left else "no"
        lines.append(
            f"| `{check.left}` | `{check.right}` | {left_to_right} | {right_to_left} | {check.status} |"
        )

    lines.extend(["", "## Directed Links Found", "", "| Source | Related system links |", "|---|---|"])
    for doc in SYSTEM_DOCS:
        refs = sorted(links[doc])
        related = ", ".join(f"`{ref}`" for ref in refs) if refs else "None"
        lines.append(f"| `MAP_System/{doc}` | {related} |")

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- Only the `## Related files` section is considered.",
            "- Whole-file mentions outside `## Related files` are intentionally ignored for this task.",
            "- Non-system files such as templates, `shared/hpom.md`, `emergence/README.md`, and `Guidelines/` are outside this pair matrix unless they are one of the 11 scoped system docs.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="MAP_System root")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Markdown report path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    output = args.output
    if not output.is_absolute():
        output = (Path.cwd() / output).resolve()
    links = load_related_links(root)
    checks = pair_checks(links)
    command = (
        "MAP_System/.venv/bin/python MAP_System/scripts/check_system_crosslinks.py "
        f"--output {repo_path(output)}"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(markdown_report(links, checks, command), encoding="utf-8")
    print(repo_path(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
