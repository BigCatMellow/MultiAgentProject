#!/usr/bin/env python3
"""Tests for agent status reconciliation."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SCRIPT = ROOT / "scripts" / "reconcile_agents.py"


def test_reconcile_reports_stale_and_unregistered_agents() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        status = base / "status.json"
        hcom = base / "hcom.json"
        status.write_text(
            json.dumps({"agents": {"codex": {"status": "available"}, "claude-old": {"status": "available"}}}),
            encoding="utf-8",
        )
        hcom.write_text(json.dumps([{"name": "codex", "status": "active"}, {"name": "new-agent", "status": "active"}]), encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--status-file", str(status), "--hcom-json", str(hcom), "--json"],
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert result.returncode == 0, result.stderr
        payload = json.loads(result.stdout)
        assert payload["durable_available_not_live"] == ["claude-old"]
        assert payload["live_not_registered"] == ["new-agent"]


def main() -> int:
    test_reconcile_reports_stale_and_unregistered_agents()
    print("PASS test_reconcile_reports_stale_and_unregistered_agents")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
