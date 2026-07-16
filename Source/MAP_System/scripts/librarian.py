#!/usr/bin/env python3
"""MAP librarian agent: wikilink resolution/validation and Related-Files
conversion for MAP_System markdown docs.

First real implementation of the "librarian agent" concept researched (not
built) in TASK-154 (BRIEF-0002/SUMMARY-0002, claude-bedrock/agentcairn
patterns). Scope is deliberately narrow for this first pass: add `[[wikilink]]`
tags alongside existing backtick-path references in "Related file(s)"
sections (additive, reversible, does not remove the path), and provide
resolution/validation/backlink-index commands a future mission-control panel
or measurement task can build on.

Does not implement summarization, staleness invalidation, or the full
Library layer -- those remain gated behind the compression/churn
measurement this script also runs (see `measure` command), per
map-library-viability-measurement.md's adoption threshold.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent

WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]")
RELATED_HEADING_PATTERN = re.compile(r"^##\s+Related\s+files?\s*$", re.IGNORECASE)
BULLET_PATH_PATTERN = re.compile(r"^(\s*-\s+)`([^`]+)`(.*)$")


def _iter_markdown_files(root: Path = ROOT) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if ".venv" not in p.parts)


def _basename_no_ext(path: Path) -> str:
    return path.stem


def build_name_index(root: Path = ROOT) -> dict[str, list[Path]]:
    """Maps a bare filename (no extension) to every markdown file with that
    stem, so `[[RESEARCH_SYSTEM]]` can resolve even without a full path.
    Ambiguous stems (more than one match) are still returned as a list so
    callers can decide/report ambiguity rather than silently picking one.
    """
    index: dict[str, list[Path]] = defaultdict(list)
    for path in _iter_markdown_files(root):
        index[_basename_no_ext(path)].append(path)
    return dict(index)


def resolve_wikilink(name: str, name_index: dict[str, list[Path]] | None = None, root: Path = ROOT) -> list[Path]:
    """Returns the list of files a wikilink name resolves to (0, 1, or many
    for an ambiguous name). Also accepts a relative path with or without
    `.md` for links that already carry a fuller path.
    """
    name_index = name_index if name_index is not None else build_name_index(root)
    # A path-shaped name ("events/README") is a caller's disambiguation of an
    # otherwise-ambiguous bare stem -- resolve it directly FIRST, before
    # falling back to stem lookup, so a specific reference doesn't get
    # dissolved back into every file sharing that stem.
    if "/" in name:
        direct = root / name if name.endswith(".md") else root / f"{name}.md"
        if direct.exists():
            return [direct]
    stem = Path(name).stem
    if stem in name_index:
        return name_index[stem]
    direct = root / name if name.endswith(".md") else root / f"{name}.md"
    if direct.exists():
        return [direct]
    return []


def validate_wikilinks_in_file(path: Path, name_index: dict[str, list[Path]] | None = None) -> list[dict]:
    """Returns a list of finding dicts for each `[[...]]` occurrence that is
    broken (resolves to nothing) or ambiguous (resolves to more than one
    file) -- both are reported, neither silently accepted.
    """
    name_index = name_index if name_index is not None else build_name_index()
    findings = []
    text = path.read_text(encoding="utf-8")
    for match in WIKILINK_PATTERN.finditer(text):
        name = match.group(1).strip()
        targets = resolve_wikilink(name, name_index)
        if len(targets) == 0:
            findings.append({"file": str(path), "link": name, "issue": "broken", "targets": []})
        elif len(targets) > 1:
            findings.append({
                "file": str(path), "link": name, "issue": "ambiguous",
                "targets": [str(t) for t in targets],
            })
    return findings


def validate_all_wikilinks(root: Path = ROOT) -> list[dict]:
    name_index = build_name_index(root)
    findings = []
    for path in _iter_markdown_files(root):
        findings.extend(validate_wikilinks_in_file(path, name_index))
    return findings


def build_backlink_index(root: Path = ROOT) -> dict[str, list[str]]:
    """Maps a resolved target file (relative path) to every source file
    that links to it -- the reverse-link index a librarian/mission-control
    panel needs to answer "what points here?"
    """
    name_index = build_name_index(root)
    backlinks: dict[str, list[str]] = defaultdict(list)
    for path in _iter_markdown_files(root):
        text = path.read_text(encoding="utf-8")
        for match in WIKILINK_PATTERN.finditer(text):
            name = match.group(1).strip()
            targets = resolve_wikilink(name, name_index)
            for target in targets:
                rel_target = str(target.relative_to(root))
                rel_source = str(path.relative_to(root))
                if rel_source not in backlinks[rel_target]:
                    backlinks[rel_target].append(rel_source)
    return dict(backlinks)


def _resolve_related_bullet_path(ref_path: str, source_file: Path, root: Path, repo: Path) -> Path | None:
    """Tries every base a Related-Files bullet's path convention actually
    uses in this repo, in order, and returns the first real `.md` file
    found. A single-base resolution (just `root / ref_path`) was TASK-174's
    original approach; it only worked for batch 1 because those 16
    root-level docs happen to cross-reference each other with bare
    filenames in the same directory as `root`. Batch 2 (files in
    subdirectories) exposed two more real conventions this must also
    handle -- found and diagnosed by a helper agent (librarian-batch2)
    during TASK-174 follow-up, not guessed:

    1. Repo-root-relative paths with an explicit `MAP_System/` prefix
       (e.g. `MAP_System/artifacts/planning/foo.md`) -- must resolve
       against `repo`, not `root`, or `root / ref_path` doubles the
       `MAP_System/` segment into a path that never exists.
    2. Bare filenames relative to the REFERENCING file's own directory
       (e.g. `emergence/README.md` linking to `SYNTHESIS_METHODS.md`,
       meaning `emergence/SYNTHESIS_METHODS.md`) -- must resolve against
       `source_file.parent`, not `root`.

    `Guidelines/`-prefixed references are deliberately NOT resolved here:
    `Guidelines/` is a separate, cross-project scope from `MAP_System/`
    per `AGENTS.md`'s routing table, and this tool's `validate`/`backlinks`
    commands are scoped to `root` (MAP_System/) by default -- wikilinking
    a path this tool can't also validate would silently produce a link
    `validate` can never confirm resolves, which is worse than leaving it
    as a plain path.
    """
    if ref_path.startswith("Guidelines/"):
        return None
    candidates = []
    if ref_path.startswith(("MAP_System/", "/")):
        candidates.append(repo / ref_path.lstrip("/"))
    else:
        candidates.append(source_file.parent / ref_path)
        candidates.append(root / ref_path)
    for candidate in candidates:
        if candidate.exists() and candidate.suffix == ".md":
            return candidate
    return None


def add_wikilinks_to_related_section(path: Path, root: Path = ROOT, repo: Path = REPO, dry_run: bool = True) -> dict:
    """Scans a file's '## Related file(s)' section for bullets shaped like
    a backtick-quoted path followed by a description, and appends a
    `[[Name]]` wikilink right after the backtick path, ONLY when that path
    resolves to a real file (checked against multiple base directories --
    see `_resolve_related_bullet_path`) and doesn't already carry a
    wikilink on that line. Additive and reversible: the original backtick
    path is never removed.
    """
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_related = False
    converted = 0
    skipped_unresolved = 0
    skipped_already_linked = 0
    skipped_out_of_scope = 0
    new_lines = []
    name_index = build_name_index(root)

    for line in lines:
        if RELATED_HEADING_PATTERN.match(line.strip()):
            in_related = True
            new_lines.append(line)
            continue
        if in_related and line.startswith("## "):
            in_related = False

        if in_related:
            match = BULLET_PATH_PATTERN.match(line)
            if match:
                prefix, ref_path, rest = match.groups()
                if "[[" in rest:
                    skipped_already_linked += 1
                    new_lines.append(line)
                    continue
                candidate = _resolve_related_bullet_path(ref_path, path, root, repo)
                if candidate is not None:
                    stem = _basename_no_ext(candidate)
                    # Use the bare stem only when it's unambiguous repo-wide
                    # (e.g. 28 different README.md files share the "README"
                    # stem) -- otherwise use the relative path (no
                    # extension) so the wikilink actually disambiguates
                    # instead of silently colliding with unrelated files.
                    if len(name_index.get(stem, [])) > 1:
                        wikilink_name = str(candidate.relative_to(root).with_suffix(""))
                    else:
                        wikilink_name = stem
                    line = f"{prefix}`{ref_path}` [[{wikilink_name}]]{rest}"
                    converted += 1
                elif ref_path.startswith("Guidelines/"):
                    skipped_out_of_scope += 1
                else:
                    skipped_unresolved += 1
        new_lines.append(line)

    result = {
        "file": str(path),
        "converted": converted,
        "skipped_unresolved": skipped_unresolved,
        "skipped_already_linked": skipped_already_linked,
        "skipped_out_of_scope": skipped_out_of_scope,
        "dry_run": dry_run,
    }
    if not dry_run and converted:
        path.write_text("\n".join(new_lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
    return result


def _tokenish_count(text: str) -> int:
    """Cheap, dependency-free token proxy: whitespace-split word count.
    Not a real tokenizer, but consistent and good enough for a relative
    compression-ratio measurement, per map-library-viability-measurement.md's
    own framing (ratio matters more than absolute token accuracy here).
    """
    return len(text.split())


def structural_summary(text: str, max_lines: int = 12) -> str:
    """Deterministic, non-LLM extractive summary: title + section headings
    + first sentence of the doc body. This is intentionally the CHEAPEST
    possible summary strategy -- a real Library layer would need better
    summarization, but this gives an honest floor measurement: if even a
    naive structural summary doesn't compress well or loses too much, a
    fancier one won't fix a false premise.
    """
    lines = text.splitlines()
    headings = [l for l in lines if l.startswith("#")]
    body_lines = [l for l in lines if l.strip() and not l.startswith("#") and not l.startswith("<!--")]
    first_para = body_lines[0] if body_lines else ""
    summary_lines = headings[:max_lines] + ([first_para] if first_para else [])
    return "\n".join(summary_lines)


def measure_compression(paths: list[Path]) -> dict:
    """Real compression-ratio measurement (Gap-Register's #1-priority,
    previously-never-run prerequisite) using the cheapest possible
    summarizer, against real MAP files -- not a simulation.
    """
    results = []
    for path in paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        summary = structural_summary(text)
        source_tokens = _tokenish_count(text)
        summary_tokens = _tokenish_count(summary)
        ratio = (source_tokens / summary_tokens) if summary_tokens else None
        results.append({
            "file": str(path),
            "source_tokens": source_tokens,
            "summary_tokens": summary_tokens,
            "compression_ratio": round(ratio, 2) if ratio else None,
        })
    ratios = sorted(r["compression_ratio"] for r in results if r["compression_ratio"])
    median = ratios[len(ratios) // 2] if ratios else None
    p90 = ratios[int(len(ratios) * 0.9)] if ratios else None
    worst = min(ratios) if ratios else None
    return {
        "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "file_count": len(results),
        "median_compression_ratio": median,
        "p90_compression_ratio": p90,
        "worst_compression_ratio": worst,
        "per_file": results,
    }


def measure_churn(paths: list[Path], since: str = "30 days ago", repo: Path = REPO) -> dict:
    """Real file-churn measurement via git log -- another Gap-Register
    prerequisite, run against actual MAP files instead of assumed.
    """
    results = []
    for path in paths:
        if not path.exists():
            continue
        rel = path.relative_to(repo)
        out = subprocess.run(
            ["git", "log", f"--since={since}", "--oneline", "--", str(rel)],
            cwd=repo, text=True, capture_output=True, check=False,
        )
        commit_count = len([l for l in out.stdout.splitlines() if l.strip()])
        results.append({"file": str(rel), "commits_since": since, "commit_count": commit_count})
    return {
        "measured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "since": since,
        "file_count": len(results),
        "per_file": results,
        "churned_file_count": sum(1 for r in results if r["commit_count"] > 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    wl_cmd = sub.add_parser("wikilink-related-files")
    wl_cmd.add_argument("file", type=Path)
    wl_cmd.add_argument("--apply", action="store_true", help="Write changes (default: dry-run report only)")

    validate_cmd = sub.add_parser("validate")
    validate_cmd.add_argument("--root", type=Path, default=ROOT)

    backlinks_cmd = sub.add_parser("backlinks")
    backlinks_cmd.add_argument("--root", type=Path, default=ROOT)

    measure_cmd = sub.add_parser("measure")
    measure_cmd.add_argument("files", nargs="+", type=Path)
    measure_cmd.add_argument("--churn-since", default="30 days ago")

    args = parser.parse_args()

    if args.command == "wikilink-related-files":
        result = add_wikilinks_to_related_section(args.file, dry_run=not args.apply)
        print(json.dumps(result, indent=2))
    elif args.command == "validate":
        findings = validate_all_wikilinks(args.root)
        print(json.dumps({"finding_count": len(findings), "findings": findings}, indent=2))
        return 1 if findings else 0
    elif args.command == "backlinks":
        print(json.dumps(build_backlink_index(args.root), indent=2))
    elif args.command == "measure":
        resolved_files = [f.resolve() for f in args.files]
        compression = measure_compression(resolved_files)
        churn = measure_churn(resolved_files, since=args.churn_since)
        print(json.dumps({"compression": compression, "churn": churn}, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
