#!/usr/bin/env python3
"""Tests for Git operation lock helper."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCRIPT = ROOT / "scripts" / "git_operation_lock.py"


def test_lock_acquire_blocks_second_owner_and_releases() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        lock = Path(tmp) / "lock.json"
        first = subprocess.run(
            [sys.executable, str(SCRIPT), "--lock-file", str(lock), "acquire", "--owner", "codex", "--operation", "push", "--stop-condition", "done"],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        second = subprocess.run(
            [sys.executable, str(SCRIPT), "--lock-file", str(lock), "acquire", "--owner", "claude", "--operation", "push", "--stop-condition", "done"],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        release = subprocess.run(
            [sys.executable, str(SCRIPT), "--lock-file", str(lock), "release", "--owner", "codex"],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert first.returncode == 0, first.stderr
        assert second.returncode == 1
        assert release.returncode == 0, release.stderr
        assert not lock.exists()


def main() -> int:
    test_lock_acquire_blocks_second_owner_and_releases()
    print("PASS test_lock_acquire_blocks_second_owner_and_releases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
