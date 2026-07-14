#!/usr/bin/env python3
"""Focused tests for validate_context_packets.py."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
VALIDATOR = ROOT / "scripts" / "validate_context_packets.py"
TEMPLATE = ROOT / "templates" / "CONTEXT_PACKET_TEMPLATE.md"


def copy_template(dst_root: Path) -> None:
    dst = dst_root / "templates"
    dst.mkdir(parents=True)
    shutil.copy2(TEMPLATE, dst / TEMPLATE.name)


def run_validator(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--root", str(root)],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def test_context_validator_accepts_template_and_no_packets() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_template(root)

        result = run_validator(root)

        assert result.returncode == 0, result.stdout + result.stderr
        assert "PASS context packet validation" in result.stdout


def test_context_validator_rejects_missing_template_fragment() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_template(root)
        template = root / "templates" / "CONTEXT_PACKET_TEMPLATE.md"
        template.write_text("# Context Packet\nPacket ID: CONTEXT-0001\n", encoding="utf-8")

        result = run_validator(root)

        assert result.returncode == 1
        assert "MISSING_FRAGMENT" in result.stdout
        assert "## Excluded" in result.stdout


def test_context_validator_rejects_submitted_packet_placeholders() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "MAP_System"
        copy_template(root)
        packet_dir = root / "artifacts" / "context-packets"
        packet_dir.mkdir(parents=True)
        packet = packet_dir / "CONTEXT-0001-placeholder.md"
        packet.write_text(
            "\n".join(
                [
                    "# Context Packet",
                    "",
                    "Packet ID: CONTEXT-0001",
                    "Anchor: TASK-000 test packet",
                    "Assembled by: codex-lab-test",
                    "Date: 2026-07-03",
                    "Status: SUBMITTED",
                    "",
                    "See `MAP_System/CONTEXT_SYSTEM.md` for the rules this packet follows.",
                    "",
                    "## Required",
                    "",
                    "- `path` - <why required>",
                    "",
                    "## Optional (trigger-gated)",
                    "",
                    "- none",
                    "",
                    "## Excluded",
                    "",
                    "- none",
                    "",
                    "## Staleness check",
                    "",
                    "- [x] No file in Required is marked superseded",
                    "",
                    "## Notes",
                    "",
                    "- ready for validation",
                ]
            )
            + "\n",
            encoding="utf-8",
        )

        result = run_validator(root)

        assert result.returncode == 1
        assert "FINAL_PLACEHOLDER" in result.stdout
        assert "<why required>" in result.stdout


def main() -> int:
    test_context_validator_accepts_template_and_no_packets()
    print("PASS test_context_validator_accepts_template_and_no_packets")
    test_context_validator_rejects_missing_template_fragment()
    print("PASS test_context_validator_rejects_missing_template_fragment")
    test_context_validator_rejects_submitted_packet_placeholders()
    print("PASS test_context_validator_rejects_submitted_packet_placeholders")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
