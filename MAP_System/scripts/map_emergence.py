#!/usr/bin/env python3
"""Create, index, and validate MAP emergence artifacts."""

from __future__ import annotations

import argparse
import contextlib
from dataclasses import dataclass
from datetime import date
import fcntl
import json
import re
import sys
from pathlib import Path

try:
    from MAP_System.scripts.redaction import guard as redaction_guard
except ModuleNotFoundError:  # direct script execution
    from redaction import guard as redaction_guard


ROOT = Path(__file__).resolve().parents[1]
EMERGENCE_DIR = ROOT / "emergence"


@dataclass(frozen=True)
class ArtifactKind:
    name: str
    prefix: str
    folder: str
    template: str
    id_label: str
    owner_label: str
    summary_section: str
    index_label: str
    default_status: str
    required_labels: tuple[str, ...]


KINDS: dict[str, ArtifactKind] = {
    "insight": ArtifactKind(
        name="insight",
        prefix="INS",
        folder="insights",
        template="INSIGHT_TEMPLATE.md",
        id_label="Insight ID",
        owner_label="Detected by",
        summary_section="Short description",
        index_label="Active Insights",
        default_status="RAW",
        required_labels=("Insight ID", "Project", "Detected by", "Date", "Status"),
    ),
    "synthesis": ArtifactKind(
        name="synthesis",
        prefix="SYN",
        folder="synthesis",
        template="SYNTHESIS_NOTE_TEMPLATE.md",
        id_label="Synthesis ID",
        owner_label="Created by",
        summary_section="New combination",
        index_label="Active Synthesis Notes",
        default_status="CLARIFIED",
        required_labels=("Synthesis ID", "Project", "Date", "Created by", "Status"),
    ),
    "idea": ArtifactKind(
        name="idea",
        prefix="IDEA",
        folder="ideas",
        template="IDEA_CARD_TEMPLATE.md",
        id_label="Idea ID",
        owner_label="Owner",
        summary_section="Idea",
        index_label="Active Idea Cards",
        default_status="CANDIDATE",
        required_labels=("Idea ID", "Project", "Owner", "Date", "Status"),
    ),
    "experiment": ArtifactKind(
        name="experiment",
        prefix="EXP",
        folder="experiments",
        template="EXPERIMENT_TEMPLATE.md",
        id_label="Experiment ID",
        owner_label="Owner",
        summary_section="Hypothesis",
        index_label="Active Experiments",
        default_status="PROPOSED",
        required_labels=("Experiment ID", "Project", "Owner", "Date", "Status"),
    ),
    "promotion": ArtifactKind(
        name="promotion",
        prefix="PROMO",
        folder="promotions",
        template="PROMOTION_RECORD_TEMPLATE.md",
        id_label="Promotion ID",
        owner_label="Decision owner",
        summary_section="What is being promoted?",
        index_label="Promotion Records",
        default_status="PROPOSED",
        required_labels=("Promotion ID", "Project", "Decision owner", "Date", "Status"),
    ),
}

PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
STALE_TEXT_RE = re.compile(r"(?im)^\s*(text|tbd|none|idea-####)\s*$")
SECTION_RE = re.compile(r"^##\s+(.+?)\s*$", re.MULTILINE)
ARTIFACT_ID_RE = re.compile(r"\b(?:INS|SYN|IDEA|EXP|PROMO)-\d{4}\b")
MAP_MD_PATH_RE = re.compile(r"\b(?:MAP_System/)?[A-Za-z0-9_./-]+\.md\b")
WIKILINK_RE = re.compile(r"\[\[[^\]]+\]\]")

SECTION_KEYS = {
    "Short description": "obs",
    "Trigger": "src",
    "The synthesis": "synth",
    "Why it might matter": "why",
    "Evidence": "ev",
    "Risk": "risk",
    "Idea": "idea",
    "Problem or opportunity": "gap",
    "Why now": "now",
    "Expected benefit": "gain",
    "Cost": "cost",
    "Smallest safe experiment": "test",
    "Hypothesis": "hyp",
    "Test": "test",
    "Scope": "scope",
    "Limits": "limits",
    "Success criteria": "pass",
    "Failure criteria": "fail",
    "New combination": "combo",
    "What this makes possible": "opens",
    "Why this was not obvious before": "why-hidden",
    "What is being promoted?": "promote",
    "Why it should become real work": "why",
    "Scope": "scope",
    "Notes": "note",
    "Pieces being combined": "pieces",
}
COMPACT_LABEL_RE = re.compile(
    r"^(?:-\s*)?(?:obs|src|synth|why|ev|risk|idea|gap|now|gain|cost|test|hyp|scope|limits|pass|fail|combo|opens|why-hidden|promote|note|pieces|use|a|b|c):\s*"
)
CHECKBOX_HEADINGS = {
    "Decision",
    "Decision needed",
    "Recommendation",
    "Recommended next action",
    "Recommended next step",
    "Reversibility",
    "What it becomes",
}
PIECE_LABELS = {
    "Piece A": "a",
    "Piece B": "b",
    "Piece C (optional)": "c",
}
CLOSED_ARTIFACT_STATUSES = {
    "ADOPTED",
    "APPROVED",
    "ARCHIVED",
    "DISMISSED",
    "PARKED",
    "PROMOTED",
    "PROMOTED_TO_TASK",
    "REJECTED",
    "SUPERSEDED",
    "WITHDRAWN",
}


class EmergenceError(RuntimeError):
    pass


def emergence_dir(root: Path) -> Path:
    return root / "emergence"


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:64] or "artifact"


def template_path(root: Path, kind: ArtifactKind) -> Path:
    return emergence_dir(root) / "templates" / kind.template


def artifact_dir(root: Path, kind: ArtifactKind) -> Path:
    return emergence_dir(root) / kind.folder


def artifact_files(root: Path, kind: ArtifactKind) -> list[Path]:
    folder = artifact_dir(root, kind)
    if not folder.exists():
        return []
    return sorted(path for path in folder.glob("*.md") if path.is_file())


def artifact_file_by_id(root: Path, artifact_id: str) -> Path | None:
    for kind in KINDS.values():
        for path in artifact_files(root, kind):
            if path.stem.startswith(f"{artifact_id}-"):
                return path
    return None


def wikilink_for_path(root: Path, path: Path) -> str | None:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return None
    if path.suffix != ".md":
        return None
    return f"[[{rel.with_suffix('').as_posix()}]]"


def compact_references(text: str, root: Path) -> str:
    """Add MAP-local wikilinks for references we can resolve safely.

    Only markdown targets get wikilinks, so `librarian.py validate` can still
    resolve them. Task JSON IDs stay plain because they are not markdown docs.
    Existing wikilinks are left untouched.
    """

    def convert_segment(segment: str) -> str:
        protected_links: dict[str, str] = {}

        def protect(link: str) -> str:
            token = f"__MAP_REF_LINK_{len(protected_links)}__"
            protected_links[token] = link
            return token

        def restore_links(value: str) -> str:
            for token, link in protected_links.items():
                value = value.replace(token, link)
            return value

        def replace_artifact(match: re.Match[str]) -> str:
            artifact_id = match.group(0)
            path = artifact_file_by_id(root, artifact_id)
            link = wikilink_for_path(root, path) if path else None
            return link or artifact_id

        def replace_path(match: re.Match[str]) -> str:
            raw = match.group(0)
            candidate = Path(raw)
            if raw.startswith("MAP_System/"):
                path = root.parent / candidate
            else:
                path = root / candidate
            if not path.exists():
                id_match = ARTIFACT_ID_RE.search(raw)
                if id_match:
                    artifact_path = artifact_file_by_id(root, id_match.group(0))
                    if artifact_path and artifact_path.name == raw:
                        path = artifact_path
            link = wikilink_for_path(root, path) if path.exists() else None
            return protect(link) if link else raw

        segment = MAP_MD_PATH_RE.sub(replace_path, segment)
        segment = ARTIFACT_ID_RE.sub(replace_artifact, segment)
        return restore_links(segment)

    parts: list[str] = []
    cursor = 0
    for match in WIKILINK_RE.finditer(text):
        parts.append(convert_segment(text[cursor:match.start()]))
        parts.append(match.group(0))
        cursor = match.end()
    parts.append(convert_segment(text[cursor:]))
    return "".join(parts)


def compact_section_value(heading: str, value: str, root: Path) -> str:
    key = SECTION_KEYS.get(heading, "note")
    lines = [line.strip() for line in value.strip().splitlines() if line.strip()]
    if not lines:
        return f"- {key}: TBD"
    if len(lines) == 1:
        return f"- {key}: {compact_references(lines[0], root)}"
    rendered = [f"- {key}: {compact_references(lines[0], root)}"]
    rendered.extend(f"- +: {compact_references(line.lstrip('- ').strip(), root)}" for line in lines[1:])
    return "\n".join(rendered)


def compact_plain_lines(lines: list[str], label: str, root: Path) -> list[str]:
    content = " ".join(line.strip() for line in lines if line.strip())
    if not content or content == "-":
        return [f"- {label}:"]
    if COMPACT_LABEL_RE.match(content) or content.startswith("- ["):
        return [content]
    return [f"- {label}: {compact_references(content, root)}"]


def compact_piece_section(body: str, root: Path) -> str:
    """Compact a synthesis 'Pieces being combined' section with ### pieces."""
    lines = body.splitlines()
    output: list[str] = []
    current_heading: str | None = None
    current_body: list[str] = []

    def flush() -> None:
        nonlocal current_heading, current_body
        if current_heading is None:
            if current_body and any(line.strip() for line in current_body):
                output.extend(compact_plain_lines(current_body, "pieces", root))
            current_body = []
            return
        output.append("")
        output.append(f"### {current_heading}")
        output.append("")
        output.extend(compact_plain_lines(current_body, PIECE_LABELS.get(current_heading, "pieces"), root))
        current_body = []

    for line in lines:
        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            flush()
            current_heading = heading.group(1)
        else:
            current_body.append(line)
    flush()
    return "\n".join(output).strip()


def compact_checkbox_section(body: str) -> str:
    kept = []
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == "Choose one:" or stripped.startswith("Can this be undone easily?"):
            continue
        kept.append(line.rstrip())
    return "\n".join(kept).strip()


def compact_record_section(heading: str, body: str, root: Path) -> str:
    stripped = body.strip()
    if heading == "Pieces being combined":
        return compact_piece_section(body, root)
    if heading in CHECKBOX_HEADINGS:
        return compact_checkbox_section(body)
    label = SECTION_KEYS.get(heading, "note")
    if stripped != "-" and "\n-" in f"\n{stripped}" and all(
        not line.strip() or line.lstrip().startswith("-") for line in stripped.splitlines()
    ):
        return stripped
    return "\n".join(compact_plain_lines(body.splitlines(), label, root)).strip()


def compact_record_text(text: str, root: Path) -> str:
    """Convert existing emergence record body sections to compact bullets.

    Header fields and section headings stay exactly as-is. The conversion is
    intentionally mechanical and conservative: it labels existing text instead
    of summarizing or inventing shorter meaning.
    """
    pattern = re.compile(r"^##\s+(.+?)\s*\n(.*?)(?=^##\s+|\Z)", re.MULTILINE | re.DOTALL)
    output: list[str] = []
    cursor = 0
    for match in pattern.finditer(text):
        output.append(text[cursor:match.start()].rstrip())
        heading = match.group(1)
        compacted = compact_record_section(heading, match.group(2), root)
        output.append(f"## {heading}\n\n{compacted}".rstrip())
        cursor = match.end()
    output.append(text[cursor:].rstrip())
    return "\n\n".join(part for part in output if part != "") + ("\n" if text.endswith("\n") else "")


def is_active_artifact(path: Path) -> bool:
    text = path.read_text(encoding="utf-8", errors="replace")
    status = extract_header(text, "Status")
    return bool(status) and status not in CLOSED_ARTIFACT_STATUSES


def resolve_compact_target(root: Path, target: str) -> Path:
    candidate = Path(target)
    if candidate.exists():
        return candidate
    root_candidate = root / target
    if root_candidate.exists():
        return root_candidate
    id_match = re.fullmatch(r"(?:INS|SYN|IDEA|EXP|PROMO)-\d{4}", target)
    if id_match:
        path = artifact_file_by_id(root, target)
        if path:
            return path
    raise EmergenceError(f"compact target not found: {target}")


def compact_targets(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    targets: list[Path] = []
    if args.all_active:
        for kind in KINDS.values():
            targets.extend(path for path in artifact_files(root, kind) if is_active_artifact(path))
    for target in args.targets:
        targets.append(resolve_compact_target(root, target))
    if not targets:
        raise EmergenceError("compact requires at least one target or --all-active")

    seen: set[Path] = set()
    results = []
    for path in targets:
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        original = path.read_text(encoding="utf-8")
        compacted = compact_record_text(original, root)
        compacted = redaction_guard(compacted, f"emergence compact {path.name}")
        changed = compacted != original
        if args.apply and changed:
            path.write_text(compacted, encoding="utf-8")
        results.append({
            "file": str(path.relative_to(root.parent) if path.is_relative_to(root.parent) else path),
            "changed": changed,
            "applied": bool(args.apply and changed),
        })

    if args.json:
        print(json.dumps({"dry_run": not args.apply, "results": results}, indent=2))
    else:
        for result in results:
            state = "applied" if result["applied"] else "would-change" if result["changed"] else "unchanged"
            print(f"{state} {result['file']}")
    return 0


def table_cell(text: str) -> str:
    return text.replace("\n", " ").replace("|", "\\|")


def strip_compact_label(text: str) -> str:
    return COMPACT_LABEL_RE.sub("", text.strip())


def compact_index_summary(text: str, max_words: int = 18) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + " ..."


@contextlib.contextmanager
def id_allocation_lock(root: Path, kind: ArtifactKind):
    """Serialize ID allocation + existence-check + write for one artifact kind.

    next_id() only scans existing filenames; without this lock, two
    concurrent `create` calls for the same kind can both read the same
    highest ID and both pass the pre-write `path.exists()` check before
    either has written, producing a silent ID collision (the same failure
    class as the REPAIR-0001 collision in repairs/, which still has no
    lock of its own today).
    """
    lock_dir = root / ".locks"
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock_path = lock_dir / f"emergence-{kind.prefix.lower()}.lock"
    with open(lock_path, "w") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def next_id(root: Path, kind: ArtifactKind) -> str:
    highest = 0
    pattern = re.compile(rf"^{re.escape(kind.prefix)}-(\d{{4}})")
    for path in artifact_files(root, kind):
        match = pattern.match(path.stem)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"{kind.prefix}-{highest + 1:04d}"


def replace_header(text: str, label: str, value: str) -> str:
    pattern = re.compile(rf"^({re.escape(label)}:\s*).*$", re.MULTILINE)
    updated, count = pattern.subn(rf"\g<1>{value}", text, count=1)
    if count == 0:
        raise EmergenceError(f"template missing header: {label}")
    return updated


def replace_section(text: str, heading: str, value: str) -> str:
    pattern = re.compile(
        rf"(^##\s+{re.escape(heading)}\s*\n)(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    updated, count = pattern.subn(rf"\g<1>\n{value.strip()}\n\n", text, count=1)
    if count == 0:
        return text
    return updated


def extract_header(text: str, label: str) -> str:
    match = re.search(rf"^{re.escape(label)}:\s*(.*?)\s*$", text, re.MULTILINE)
    return match.group(1).strip() if match else ""


def extract_section(text: str, heading: str) -> str:
    pattern = re.compile(
        rf"^##\s+{re.escape(heading)}\s*\n(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    match = pattern.search(text)
    if not match:
        return ""
    lines = [
        line.strip()
        for line in match.group(1).strip().splitlines()
        if line.strip() and not PLACEHOLDER_RE.search(line)
    ]
    return " ".join(lines).strip("- ").strip()


def detect_kind(path: Path) -> ArtifactKind | None:
    stem = path.stem
    for kind in KINDS.values():
        if stem.startswith(f"{kind.prefix}-"):
            return kind
    return None


def fill_template(root: Path, kind: ArtifactKind, args: argparse.Namespace, artifact_id: str) -> str:
    path = template_path(root, kind)
    if not path.exists():
        raise EmergenceError(f"template not found: {path}")
    text = path.read_text(encoding="utf-8")
    today = args.date or date.today().isoformat()
    status = args.status or kind.default_status

    replacements = {
        kind.id_label: artifact_id,
        "Project": args.project,
        kind.owner_label: args.owner,
        "Date": today,
        "Status": status,
        "Related task": args.related_task or "NONE",
        "Source insight or synthesis": args.source or "NONE",
        "Source idea": args.source or "NONE",
        "Source experiment": args.source_experiment or "NONE",
    }
    for label, value in replacements.items():
        if re.search(rf"^{re.escape(label)}:", text, re.MULTILINE):
            text = replace_header(text, label, value)

    section_values = {
        kind.summary_section: args.summary,
        "Trigger": args.trigger or "Created from command-center emergence capture.",
        "The synthesis": args.synthesis or args.summary,
        "Why it might matter": args.why or "Could improve command-center clarity, routing, or durable memory.",
        "Evidence": args.evidence or "Captured through MAP emergence CLI.",
        "Risk": args.risk or "Acting without promotion could bypass HPOM governance.",
        "Problem or opportunity": args.problem or args.summary,
        "Why now": args.why_now or "The Command Center Lab is actively testing emergence workflow.",
        "Expected benefit": args.benefit or "Lower-friction capture and safer promotion of useful ideas.",
        "Cost": args.cost or "Small maintenance cost for CLI and validation behavior.",
        "Smallest safe experiment": args.experiment or "Create and validate file-backed emergence records.",
        "Hypothesis": args.summary,
        "Test": args.test or "Run the bounded command or workflow described by this record.",
        "Scope": args.scope or "Only the files and artifacts named in this record.",
        "Limits": args.limits or "Do not bypass HPOM task, review, or release gates.",
        "Success criteria": args.success or "The record produces useful evidence without expanding scope.",
        "Failure criteria": args.failure or "The record is unclear, unused, or creates unsafe ambiguity.",
        "New combination": args.summary,
        "What this makes possible": args.benefit or "A safer path from observation to approved MAP work.",
        "What is being promoted?": args.summary,
        "Why it should become real work": args.why or args.evidence or args.summary,
    }
    for heading, value in section_values.items():
        if value:
            text = replace_section(text, heading, compact_section_value(heading, value, root))

    return PLACEHOLDER_RE.sub("TBD", text)


def create_artifact(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    kind = KINDS[args.kind]
    with id_allocation_lock(root, kind):
        artifact_id = args.artifact_id or next_id(root, kind)
        if not re.fullmatch(rf"{re.escape(kind.prefix)}-\d{{4}}", artifact_id):
            raise EmergenceError(f"invalid {kind.name} id: {artifact_id}")
        folder = artifact_dir(root, kind)
        folder.mkdir(parents=True, exist_ok=True)
        slug = args.slug or slugify(args.summary)
        path = folder / f"{artifact_id}-{slug}.md"
        if path.exists():
            raise EmergenceError(f"artifact already exists: {path}")
        text = fill_template(root, kind, args, artifact_id)
        text = redaction_guard(text, f"emergence create {artifact_id}")
        path.write_text(text, encoding="utf-8")
    rebuild_index_for_root(root)
    print(path.relative_to(root.parent))
    return 0


def create_short_artifact(args: argparse.Namespace) -> int:
    args.kind = args.command
    args.summary = args.text
    args.artifact_id = None
    args.date = args.date or date.today().isoformat()
    args.status = args.status or None
    args.slug = args.slug or None
    args.related_task = args.related_task or None
    args.source = args.source or None
    args.source_experiment = None
    args.trigger = args.trigger or None
    args.synthesis = args.synthesis or None
    args.why = args.why or None
    args.evidence = args.evidence or None
    args.risk = args.risk or None
    args.problem = args.problem or None
    args.why_now = args.why_now or None
    args.benefit = args.benefit or None
    args.cost = args.cost or None
    args.experiment = args.experiment or None
    args.test = args.test or None
    args.scope = args.scope or None
    args.limits = args.limits or None
    args.success = args.success or None
    args.failure = args.failure or None
    return create_artifact(args)


def promote_short(args: argparse.Namespace) -> int:
    args.kind = "promotion"
    args.artifact_id = None
    args.summary = args.summary or f"Promote {args.idea_id} into HPOM review."
    args.date = args.date or date.today().isoformat()
    args.status = args.status or "PROPOSED"
    args.slug = args.slug or slugify(args.idea_id)
    args.related_task = None
    args.source = args.idea_id
    args.source_experiment = args.source_experiment or "NONE"
    args.trigger = None
    args.synthesis = None
    args.why = args.why or None
    args.evidence = args.evidence or None
    args.risk = None
    args.problem = None
    args.why_now = None
    args.benefit = None
    args.cost = None
    args.experiment = None
    args.test = None
    args.scope = None
    args.limits = None
    args.success = None
    args.failure = None
    return create_artifact(args)


def validate_artifact(path: Path, root: Path) -> list[str]:
    kind = detect_kind(path)
    if kind is None:
        return [f"{path}: unknown artifact id prefix"]
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []
    artifact_id = extract_header(text, kind.id_label)
    if not artifact_id:
        issues.append(f"{path}: missing {kind.id_label}")
    elif not path.stem.startswith(artifact_id):
        issues.append(f"{path}: filename does not start with {artifact_id}")
    for label in kind.required_labels:
        value = extract_header(text, label)
        if not value or PLACEHOLDER_RE.search(value):
            issues.append(f"{path}: invalid {label}")
    if PLACEHOLDER_RE.search(text):
        issues.append(f"{path}: unresolved template placeholders")
    summary = extract_section(text, kind.summary_section)
    if not summary:
        issues.append(f"{path}: missing summary section {kind.summary_section}")
    try:
        path.relative_to(emergence_dir(root))
    except ValueError:
        issues.append(f"{path}: outside emergence directory")
    return issues


def validate(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    issues: list[str] = []
    for kind in KINDS.values():
        for path in artifact_files(root, kind):
            issues.extend(validate_artifact(path, root))
    if issues:
        for issue in issues:
            print(f"FAIL {issue}", file=sys.stderr)
        return 1
    total = sum(len(artifact_files(root, kind)) for kind in KINDS.values())
    print(f"OK emergence artifacts valid ({total} checked)")
    return 0


def task_statuses(task_graph: Path) -> dict[str, str]:
    if not task_graph.exists():
        return {}
    payload = json.loads(task_graph.read_text(encoding="utf-8"))
    return {
        task["task_id"]: task.get("status", "UNKNOWN")
        for task in payload.get("tasks", [])
        if task.get("task_id")
    }


def stale_findings(root: Path, task_graph: Path) -> list[str]:
    findings: list[str] = []
    statuses = task_statuses(task_graph)
    closed_task_statuses = {"APPROVED", "DONE", "RELEASED"}
    open_artifact_statuses = {"RAW", "CANDIDATE", "PROPOSED"}
    closed_artifact_statuses = {
        "ADOPTED",
        "APPROVED",
        "ARCHIVED",
        "DISMISSED",
        "PARKED",
        "PROMOTED",
        "PROMOTED_TO_TASK",
        "REJECTED",
        "SUPERSEDED",
        "WITHDRAWN",
    }

    for kind in KINDS.values():
        for path in artifact_files(root, kind):
            text = path.read_text(encoding="utf-8", errors="replace")
            rel = path.relative_to(root)
            status = extract_header(text, "Status")
            related_task = extract_header(text, "Related task")
            summary = extract_section(text, kind.summary_section)
            semantic_summary = strip_compact_label(summary)

            if status in closed_artifact_statuses:
                continue
            if semantic_summary and STALE_TEXT_RE.fullmatch(semantic_summary):
                findings.append(f"{rel}: placeholder summary content {semantic_summary!r}")
            if re.search(r"\bIDEA-####\b", text):
                findings.append(f"{rel}: dangling IDEA-#### placeholder")
            if kind.name == "promotion":
                source = extract_header(text, "Source idea")
                if source and source != "NONE" and not re.fullmatch(r"IDEA-\d{4}", source):
                    findings.append(f"{rel}: invalid Source idea {source!r}")
                if re.search(r"Approved by:\s*TBD|Date:\s*TBD", text):
                    findings.append(f"{rel}: proposed promotion has incomplete approval fields")
            if related_task and related_task != "NONE":
                task_status = statuses.get(related_task)
                if task_status in closed_task_statuses and status in open_artifact_statuses:
                    findings.append(
                        f"{rel}: related task {related_task} is {task_status} but artifact remains {status}"
                    )
                elif task_status is None and related_task.startswith("TASK-"):
                    findings.append(f"{rel}: related task {related_task} not found in task graph")
    return findings


def stale(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    task_graph = args.task_graph or (root / "workflow" / "task_graph.json")
    findings = stale_findings(root, task_graph)
    if args.json:
        print(json.dumps({"findings": findings, "count": len(findings)}, indent=2))
    else:
        if findings:
            print("Emergence stale/content findings:")
            for finding in findings:
                print(f"- {finding}")
        else:
            print("No emergence stale/content findings.")
    return 1 if findings and args.strict else 0


def index_row(root: Path, kind: ArtifactKind, path: Path) -> tuple[str, str, str, str, str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    artifact_id = extract_header(text, kind.id_label) or path.stem.split("-", 2)[0]
    project = extract_header(text, "Project") or "UNKNOWN"
    owner = extract_header(text, kind.owner_label) or "UNKNOWN"
    status = extract_header(text, "Status") or "UNKNOWN"
    day = extract_header(text, "Date") or "UNKNOWN"
    summary = compact_index_summary(compact_references(extract_section(text, kind.summary_section) or path.stem, root))
    rel = path.relative_to(emergence_dir(root))
    link = f"[{artifact_id}]({rel.as_posix()})"
    return link, table_cell(project), table_cell(summary), table_cell(status), table_cell(owner), table_cell(day)


def section_lines(root: Path, kind: ArtifactKind) -> list[str]:
    paths = artifact_files(root, kind)
    if not paths:
        if kind.name == "promotion":
            return ["| - | - | No promotions yet | - | - | - |"]
        noun = kind.index_label.lower()
        return [f"| - | - | No {noun} | - | - | - |"]
    rows = []
    for path in paths:
        artifact_id, project, summary, status, owner, day = index_row(root, kind, path)
        if kind.name == "promotion":
            rows.append(f"| {artifact_id} | {project} | {summary} | HPOM / decision gate | {status} | {day} |")
        else:
            rows.append(f"| {artifact_id} | {project} | {summary} | {status} | {owner} | {day} |")
    return rows


def rebuild_index_for_root(root: Path) -> Path:
    index = emergence_dir(root) / "INDEX.md"
    lines = [
        "# Emergence System Index",
        "",
        "- src: generated by `MAP_System/scripts/map_emergence.py rebuild-index`",
        "- mode: compact registry; load full artifact only when needed",
        "- refs: artifact IDs and MAP markdown paths wikilink where resolvable",
        "",
    ]
    for kind_name in ["insight", "synthesis", "idea", "experiment"]:
        kind = KINDS[kind_name]
        lines.extend(
            [
                f"## {kind.index_label}",
                "",
                "| ID | Project | Summary | Status | Owner | Date |",
                "|---|---|---|---|---|---|",
                *section_lines(root, kind),
                "",
            ]
        )
    kind = KINDS["promotion"]
    lines.extend(
        [
            "## Promotion Records",
            "",
            "| ID | Project | Summary | Promotes into | Status | Date |",
            "|---|---|---|---|---|---|",
            *section_lines(root, kind),
            "",
            "---",
            "",
            "## ID format",
            "",
            "- Insights: `INS-0001`, `INS-0002`, ...",
            "- Synthesis: `SYN-0001`, `SYN-0002`, ...",
            "- Ideas: `IDEA-0001`, `IDEA-0002`, ...",
            "- Experiments: `EXP-0001`, `EXP-0002`, ...",
            "- Promotions: `PROMO-0001`, `PROMO-0002`, ...",
            "",
            "IDs are system-wide, not per-project.",
            "",
            "## Status quick-reference",
            "",
            "**Insight:** RAW -> CLARIFIED -> LINKED -> PARKED / PROMOTED / DISMISSED / SUPERSEDED",
            "",
            "**Idea:** CANDIDATE -> PROMISING -> NEEDS_EVIDENCE -> APPROVED_FOR_EXPERIMENT -> PARKED / REJECTED / PROMOTED_TO_TASK",
            "",
            "**Experiment:** PROPOSED -> APPROVED -> RUNNING -> SUBMITTED -> REVIEWED -> ADOPTED / REJECTED / ARCHIVED",
            "",
        ]
    )
    index.write_text("\n".join(lines), encoding="utf-8")
    return index


def rebuild_index(args: argparse.Namespace) -> int:
    path = rebuild_index_for_root(args.root.resolve())
    print(path.relative_to(args.root.resolve().parent))
    return 0


def list_index(args: argparse.Namespace) -> int:
    index = emergence_dir(args.root.resolve()) / "INDEX.md"
    if not index.exists():
        rebuild_index_for_root(args.root.resolve())
    print(index.read_text(encoding="utf-8"), end="")
    return 0


def add_short_capture_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("text", help="Artifact summary text")
    parser.add_argument("--project", default="MAP")
    parser.add_argument("--owner", default="command-center")
    parser.add_argument("--date")
    parser.add_argument("--status")
    parser.add_argument("--slug")
    parser.add_argument("--related-task")
    parser.add_argument("--source")
    parser.add_argument("--trigger")
    parser.add_argument("--synthesis")
    parser.add_argument("--why")
    parser.add_argument("--evidence")
    parser.add_argument("--risk")
    parser.add_argument("--problem")
    parser.add_argument("--why-now")
    parser.add_argument("--benefit")
    parser.add_argument("--cost")
    parser.add_argument("--experiment")
    parser.add_argument("--test")
    parser.add_argument("--scope")
    parser.add_argument("--limits")
    parser.add_argument("--success")
    parser.add_argument("--failure")
    parser.set_defaults(func=create_short_artifact)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="MAP_System root")
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create")
    create.add_argument("kind", choices=sorted(KINDS))
    create.add_argument("--artifact-id")
    create.add_argument("--project", required=True)
    create.add_argument("--owner", required=True)
    create.add_argument("--summary", required=True)
    create.add_argument("--date")
    create.add_argument("--status")
    create.add_argument("--slug")
    create.add_argument("--related-task")
    create.add_argument("--source")
    create.add_argument("--source-experiment")
    create.add_argument("--trigger")
    create.add_argument("--synthesis")
    create.add_argument("--why")
    create.add_argument("--evidence")
    create.add_argument("--risk")
    create.add_argument("--problem")
    create.add_argument("--why-now")
    create.add_argument("--benefit")
    create.add_argument("--cost")
    create.add_argument("--experiment")
    create.add_argument("--test")
    create.add_argument("--scope")
    create.add_argument("--limits")
    create.add_argument("--success")
    create.add_argument("--failure")
    create.set_defaults(func=create_artifact)

    rebuild = sub.add_parser("rebuild-index")
    rebuild.set_defaults(func=rebuild_index)

    list_cmd = sub.add_parser("list")
    list_cmd.set_defaults(func=list_index)

    check = sub.add_parser("validate")
    check.set_defaults(func=validate)

    stale_cmd = sub.add_parser("stale", help="Report stale or placeholder emergence records")
    stale_cmd.add_argument("--task-graph", type=Path)
    stale_cmd.add_argument("--json", action="store_true")
    stale_cmd.add_argument("--strict", action="store_true", help="Exit non-zero when findings exist")
    stale_cmd.set_defaults(func=stale)

    compact_cmd = sub.add_parser("compact", help="Compact existing emergence record body sections")
    compact_cmd.add_argument("targets", nargs="*", help="Record path or artifact ID")
    compact_cmd.add_argument("--all-active", action="store_true", help="Compact every non-closed emergence record")
    compact_cmd.add_argument("--apply", action="store_true", help="Write changes (default: dry-run)")
    compact_cmd.add_argument("--json", action="store_true")
    compact_cmd.set_defaults(func=compact_targets)

    for kind in ["insight", "idea", "experiment", "synthesis"]:
        short = sub.add_parser(kind)
        add_short_capture_args(short)

    promote = sub.add_parser("promote")
    promote.add_argument("idea_id")
    promote.add_argument("--project", default="MAP")
    promote.add_argument("--owner", default="command-center")
    promote.add_argument("--summary")
    promote.add_argument("--date")
    promote.add_argument("--status")
    promote.add_argument("--slug")
    promote.add_argument("--source-experiment")
    promote.add_argument("--why")
    promote.add_argument("--evidence")
    promote.set_defaults(func=promote_short)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        return args.func(args)
    except (EmergenceError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
