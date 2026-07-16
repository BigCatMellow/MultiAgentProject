#!/usr/bin/env python3
"""Tests for emergence stale/content reporting."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCRIPT = ROOT / "scripts" / "map_emergence.py"


def seed(base: Path) -> Path:
    root = base / "MAP_System"
    emergence = root / "emergence"
    shutil.copytree(ROOT / "emergence" / "templates", emergence / "templates")
    for folder in ["insights", "synthesis", "ideas", "experiments", "promotions"]:
        (emergence / folder).mkdir(parents=True)
    (root / "workflow").mkdir()
    (root / "workflow" / "task_graph.json").write_text(
        '{"project_id":"TEST","tasks":[{"task_id":"TASK-001","status":"RELEASED"}]}',
        encoding="utf-8",
    )
    return root


def run_cmd(*args: str, root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def test_stale_flags_placeholder_and_closed_related_task() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = seed(Path(tmp))
        create = run_cmd(
            "insight",
            "text",
            "--owner",
            "codex",
            "--related-task",
            "TASK-001",
            root=root,
        )
        assert create.returncode == 0, create.stderr

        stale = run_cmd("stale", "--strict", root=root)

        assert stale.returncode == 1
        assert "placeholder summary" in stale.stdout
        assert "TASK-001 is RELEASED" in stale.stdout


def main() -> int:
    test_stale_flags_placeholder_and_closed_related_task()
    print("PASS test_stale_flags_placeholder_and_closed_related_task")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
