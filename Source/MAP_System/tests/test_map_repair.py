#!/usr/bin/env python3
"""Focused tests for map_repair.py."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCRIPT = ROOT / "scripts" / "map_repair.py"


def run_cmd(*args: str, root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(root), *args],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def create_args(*, repair_id: str = "auto", summary: str = "Fix drift") -> list[str]:
    return [
        "create",
        "--repair-id", repair_id,
        "--found-by", "codex-test",
        "--severity", "DRIFT",
        "--summary", summary,
        "--surfaced-by", "unit test",
        "--severity-rationale", "mechanical drift",
        "--fix", "applied fix",
        "--verification", "focused test passed",
    ]


def test_create_explicit_repair_record() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        result = run_cmd(*create_args(repair_id="REPAIR-0042", summary="Explicit repair"), root=root)
        assert result.returncode == 0, result.stderr
        path = root.parent / result.stdout.strip()
        text = path.read_text(encoding="utf-8")
        assert "Repair ID: REPAIR-0042" in text
        assert "Explicit repair" in text


def test_auto_repair_id_allocates_next_number() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        repair_dir = root / "repairs"
        repair_dir.mkdir(parents=True)
        (repair_dir / "REPAIR-0007-existing.md").write_text("Repair ID: REPAIR-0007\n", encoding="utf-8")

        result = run_cmd(*create_args(summary="Auto repair"), root=root)

        assert result.returncode == 0, result.stderr
        assert "REPAIR-0008-auto-repair.md" in result.stdout
        assert (repair_dir / "REPAIR-0008-auto-repair.md").exists()


def test_auto_repair_id_is_atomic_under_concurrency() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"

        def create_one(index: int) -> str:
            result = run_cmd(*create_args(summary=f"Concurrent repair {index}"), root=root)
            assert result.returncode == 0, result.stderr
            return result.stdout.strip()

        with ThreadPoolExecutor(max_workers=8) as pool:
            outputs = list(pool.map(create_one, range(12)))

        assert len(outputs) == 12
        ids = sorted(path.split("/")[-1].split("-")[1] for path in outputs)
        assert ids == [f"{i:04d}" for i in range(1, 13)]
        files = sorted((root / "repairs").glob("REPAIR-*.md"))
        assert len(files) == 12
        assert len({path.name[:11] for path in files}) == 12


def main() -> int:
    tests = [
        test_create_explicit_repair_record,
        test_auto_repair_id_allocates_next_number,
        test_auto_repair_id_is_atomic_under_concurrency,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
