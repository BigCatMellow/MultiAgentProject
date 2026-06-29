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
        test_short_lab_contract,
    ]:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
