#!/usr/bin/env python3
"""Tests for MAP emergence artifact tooling."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCRIPT = ROOT / "scripts" / "map_emergence.py"


def seed_emergence_tree(base: Path) -> Path:
    root = base / "MAP_System"
    emergence = root / "emergence"
    shutil.copytree(ROOT / "emergence" / "templates", emergence / "templates")
    for folder in ["insights", "synthesis", "ideas", "experiments", "promotions"]:
        (emergence / folder).mkdir(parents=True)
    return root


def run_cmd(*args: str, root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_create_all_kinds_and_rebuild_index() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed_emergence_tree(Path(tmp))
        created = []
        for kind in ["insight", "synthesis", "idea", "experiment", "promotion"]:
            result = run_cmd(
                "create",
                kind,
                "--project",
                "MAP",
                "--owner",
                "codex-test",
                "--summary",
                f"Test {kind} summary",
                "--date",
                "2026-06-29",
                "--slug",
                f"test-{kind}",
                root=root,
            )
            assert result.returncode == 0, result.stderr
            created.append(result.stdout.strip())

        result = run_cmd("rebuild-index", root=root)
        assert result.returncode == 0, result.stderr
        index = (root / "emergence" / "INDEX.md").read_text(encoding="utf-8")
        assert "INS-0001" in index
        assert "SYN-0001" in index
        assert "IDEA-0001" in index
        assert "EXP-0001" in index
        assert "PROMO-0001" in index
        assert "Test idea summary" in index
        assert len(created) == 5


def test_validate_rejects_unresolved_placeholders() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed_emergence_tree(Path(tmp))
        bad = root / "emergence" / "insights" / "INS-0001-bad.md"
        bad.write_text((ROOT / "emergence" / "templates" / "INSIGHT_TEMPLATE.md").read_text(encoding="utf-8"), encoding="utf-8")

        result = run_cmd("validate", root=root)

        assert result.returncode == 1
        assert "unresolved template placeholders" in result.stderr


def test_validate_accepts_created_artifact() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed_emergence_tree(Path(tmp))
        create = run_cmd(
            "create",
            "idea",
            "--project",
            "MAP",
            "--owner",
            "codex-test",
            "--summary",
            "A useful command center idea",
            "--date",
            "2026-06-29",
            root=root,
        )
        assert create.returncode == 0, create.stderr

        result = run_cmd("validate", root=root)

        assert result.returncode == 0, result.stderr
        assert "OK emergence artifacts valid (1 checked)" in result.stdout


def test_created_artifact_uses_compact_sections_and_wikilinks_paths() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed_emergence_tree(Path(tmp))
        (root / "emergence" / "README.md").write_text("# Emergence\n", encoding="utf-8")

        create = run_cmd(
            "create",
            "insight",
            "--project",
            "MAP",
            "--owner",
            "codex-test",
            "--summary",
            "Capture uses MAP_System/emergence/README.md",
            "--date",
            "2026-06-29",
            "--slug",
            "compact-link",
            root=root,
        )

        assert create.returncode == 0, create.stderr
        path = root.parent / create.stdout.strip()
        text = path.read_text(encoding="utf-8")
        assert "- obs: Capture uses [[emergence/README]]" in text
        assert "What did the agent notice?" not in text


def test_rebuild_index_compacts_resolvable_emergence_references() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed_emergence_tree(Path(tmp))
        insight = run_cmd(
            "create",
            "insight",
            "--project",
            "MAP",
            "--owner",
            "codex-test",
            "--summary",
            "Seed insight",
            "--date",
            "2026-06-29",
            "--slug",
            "seed",
            root=root,
        )
        assert insight.returncode == 0, insight.stderr

        idea = run_cmd(
            "create",
            "idea",
            "--project",
            "MAP",
            "--owner",
            "codex-test",
            "--summary",
            "Follow INS-0001 with a deliberately long index-facing summary that should stay compact by pointing to the full artifact",
            "--date",
            "2026-06-29",
            "--slug",
            "follow",
            root=root,
        )
        assert idea.returncode == 0, idea.stderr

        rebuild = run_cmd("rebuild-index", root=root)
        assert rebuild.returncode == 0, rebuild.stderr
        index = (root / "emergence" / "INDEX.md").read_text(encoding="utf-8")
        assert "[[emergence/insights/INS-0001-seed]]" in index
        assert "..." in index
        assert "pointing to the full artifact" not in index
        assert "- mode: compact registry" in index


def test_reference_compaction_prefers_full_markdown_paths_over_embedded_ids() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed_emergence_tree(Path(tmp))
        insight = run_cmd(
            "create",
            "insight",
            "--project",
            "MAP",
            "--owner",
            "codex-test",
            "--summary",
            "Seed insight",
            "--date",
            "2026-06-29",
            "--slug",
            "seed",
            root=root,
        )
        assert insight.returncode == 0, insight.stderr

        idea = run_cmd(
            "create",
            "idea",
            "--project",
            "MAP",
            "--owner",
            "codex-test",
            "--summary",
            "See emergence/insights/INS-0001-seed.md",
            "--date",
            "2026-06-29",
            "--slug",
            "path-ref",
            root=root,
        )
        assert idea.returncode == 0, idea.stderr
        path = root.parent / idea.stdout.strip()
        text = path.read_text(encoding="utf-8")
        assert "[[emergence/insights/INS-0001-seed]]" in text
        assert "[[emergence/insights/INS-0001-seed]]-seed.md" not in text


def test_reference_compaction_resolves_bare_emergence_artifact_filenames() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed_emergence_tree(Path(tmp))
        insight = run_cmd(
            "create",
            "insight",
            "--project",
            "MAP",
            "--owner",
            "codex-test",
            "--summary",
            "Seed insight",
            "--date",
            "2026-06-29",
            "--slug",
            "seed",
            root=root,
        )
        assert insight.returncode == 0, insight.stderr

        idea = run_cmd(
            "create",
            "idea",
            "--project",
            "MAP",
            "--owner",
            "codex-test",
            "--summary",
            "See INS-0001-seed.md",
            "--date",
            "2026-06-29",
            "--slug",
            "bare-file-ref",
            root=root,
        )
        assert idea.returncode == 0, idea.stderr
        path = root.parent / idea.stdout.strip()
        text = path.read_text(encoding="utf-8")
        assert "[[emergence/insights/INS-0001-seed]]" in text
        assert "[[emergence/insights/INS-0001-seed]]-seed.md" not in text


def test_compact_existing_record_dry_run_apply_and_idempotent() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed_emergence_tree(Path(tmp))
        path = root / "emergence" / "insights" / "INS-0001-prose.md"
        path.write_text(
            "\n".join([
                "# Insight Record",
                "",
                "Insight ID: INS-0001",
                "Project: MAP",
                "Related task: NONE",
                "Detected by: codex-test",
                "Date: 2026-07-14",
                "Status: RAW",
                "",
                "## Short description",
                "",
                "A long observation that should become a labeled bullet.",
                "",
                "## Recommended next action",
                "",
                "Choose one:",
                "",
                "- [ ] Ignore — not worth preserving",
                "- [x] Create idea card — needs more development",
                "",
                "## Notes",
                "",
                "-",
                "",
            ]),
            encoding="utf-8",
        )
        original = path.read_text(encoding="utf-8")

        dry_run = run_cmd("compact", "INS-0001", root=root)
        assert dry_run.returncode == 0, dry_run.stderr
        assert "would-change" in dry_run.stdout
        assert path.read_text(encoding="utf-8") == original

        apply = run_cmd("compact", "INS-0001", "--apply", root=root)
        assert apply.returncode == 0, apply.stderr
        text = path.read_text(encoding="utf-8")
        assert "- obs: A long observation that should become a labeled bullet." in text
        assert "- [x] Create idea card" in text
        assert "Choose one:" not in text
        assert "## Notes\n\n- note:" in text

        second = run_cmd("compact", "INS-0001", "--apply", root=root)
        assert second.returncode == 0, second.stderr
        assert "unchanged" in second.stdout


def test_compact_all_active_skips_closed_records() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed_emergence_tree(Path(tmp))
        active = root / "emergence" / "ideas" / "IDEA-0001-active.md"
        active.write_text(
            "# Idea Card\n\n"
            "Idea ID: IDEA-0001\nProject: MAP\nSource insight or synthesis: NONE\n"
            "Owner: codex-test\nDate: 2026-07-14\nStatus: CANDIDATE\n\n"
            "## Idea\n\nNeeds compacting.\n",
            encoding="utf-8",
        )
        closed = root / "emergence" / "ideas" / "IDEA-0002-closed.md"
        closed.write_text(
            "# Idea Card\n\n"
            "Idea ID: IDEA-0002\nProject: MAP\nSource insight or synthesis: NONE\n"
            "Owner: codex-test\nDate: 2026-07-14\nStatus: REJECTED\n\n"
            "## Idea\n\nDo not compact.\n",
            encoding="utf-8",
        )

        result = run_cmd("compact", "--all-active", "--apply", root=root)
        assert result.returncode == 0, result.stderr
        assert "- idea: Needs compacting." in active.read_text(encoding="utf-8")
        assert "Do not compact." in closed.read_text(encoding="utf-8")
        assert "- idea: Do not compact." not in closed.read_text(encoding="utf-8")


def test_compact_synthesis_piece_sections() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed_emergence_tree(Path(tmp))
        path = root / "emergence" / "synthesis" / "SYN-0001-pieces.md"
        path.write_text(
            "# Synthesis Note\n\n"
            "Synthesis ID: SYN-0001\nProject: MAP\nRelated insights:\n- INS-0001\n\n"
            "Date: 2026-07-14\nCreated by: codex-test\nStatus: CLARIFIED\n\n"
            "## Pieces being combined\n\n"
            "### Piece A\n\n"
            "First long piece.\n\n"
            "### Piece B\n\n"
            "Second long piece.\n",
            encoding="utf-8",
        )

        result = run_cmd("compact", "SYN-0001", "--apply", root=root)
        assert result.returncode == 0, result.stderr
        text = path.read_text(encoding="utf-8")
        assert "### Piece A\n\n- a: First long piece." in text
        assert "### Piece B\n\n- b: Second long piece." in text

        second = run_cmd("compact", "SYN-0001", "--apply", root=root)
        assert second.returncode == 0, second.stderr
        assert "unchanged" in second.stdout


def test_short_lab_contract() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed_emergence_tree(Path(tmp))
        insight = run_cmd(
            "insight",
            "Short capture text",
            "--owner",
            "codex-test",
            "--related-task",
            "TASK-X",
            root=root,
        )
        assert insight.returncode == 0, insight.stderr
        idea = run_cmd(
            "idea",
            "Short idea text",
            "--owner",
            "codex-test",
            "--source",
            "INS-0001",
            root=root,
        )
        assert idea.returncode == 0, idea.stderr
        promote = run_cmd(
            "promote",
            "IDEA-0001",
            "--owner",
            "command-center",
            "--summary",
            "Promote short idea",
            root=root,
        )
        assert promote.returncode == 0, promote.stderr

        listing = run_cmd("list", root=root)
        assert listing.returncode == 0, listing.stderr
        assert "Short capture text" in listing.stdout
        assert "Short idea text" in listing.stdout
        assert "Promote short idea" in listing.stdout

        validate = run_cmd("validate", root=root)
        assert validate.returncode == 0, validate.stderr


def main() -> int:
    for test in [
        test_create_all_kinds_and_rebuild_index,
        test_validate_rejects_unresolved_placeholders,
        test_validate_accepts_created_artifact,
        test_created_artifact_uses_compact_sections_and_wikilinks_paths,
        test_rebuild_index_compacts_resolvable_emergence_references,
        test_reference_compaction_prefers_full_markdown_paths_over_embedded_ids,
        test_reference_compaction_resolves_bare_emergence_artifact_filenames,
        test_compact_existing_record_dry_run_apply_and_idempotent,
        test_compact_all_active_skips_closed_records,
        test_compact_synthesis_piece_sections,
        test_short_lab_contract,
    ]:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
