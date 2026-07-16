#!/usr/bin/env python3
"""Tests for MAP operator intake dispatch packets."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
INTAKE = ROOT / "scripts" / "intake_request.py"

sys.path.insert(0, str(REPO))

from MAP_System.scripts.intake_request import dispatch_packet  # noqa: E402


def test_build_request_emits_decomposer_fields() -> None:
    packet = dispatch_packet("Build the new validator halt gate", owner="codex-test")

    classification = packet["classification"]
    contract = packet["decomposer_contract"]
    assert classification["task_type"] == "implementation"
    assert classification["worker_fit"] == "codex"
    assert classification["needs_task"] == "yes"
    assert "output_paths" in contract["required_fields"]
    assert "rollback_expectation" in contract["required_fields"]
    assert contract["subtasks"][0]["routing_lane"] == "core"


def test_publish_request_requires_approval() -> None:
    packet = dispatch_packet("Push and publish the release")
    classification = packet["classification"]

    assert classification["risk"] == "repo_global"
    assert classification["needs_approval"] == "yes"
    assert "repo-global" in classification["approval_reason"]


def test_unclear_request_routes_to_shaping() -> None:
    packet = dispatch_packet("Maybe make MAP better somehow")
    classification = packet["classification"]

    assert classification["task_tier"] == "shaping"
    assert classification["gap_score"] == "high"
    assert classification["decomposition_required"] == "yes"


def test_cli_json_contains_dispatch_packet() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(INTAKE),
            "--json",
            "--owner",
            "codex-test",
            "Review the event log",
        ],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["owner"] == "codex-test"
    assert payload["entrypoint"] == "command-center-intake"
    assert payload["classification"]["task_type"] == "audit"
    assert "hcom_inform" in payload


def main() -> int:
    tests = [
        test_build_request_emits_decomposer_fields,
        test_publish_request_requires_approval,
        test_unclear_request_routes_to_shaping,
        test_cli_json_contains_dispatch_packet,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
