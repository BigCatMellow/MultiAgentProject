#!/usr/bin/env python3
"""Tests for TASK-201 bounded halt-authority windows."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.halt_state import (  # noqa: E402
    halt_authority_window_status,
    load_halt_state,
)
from MAP_System.scripts.validate_layer1 import maybe_set_halt as layer1_maybe_set_halt  # noqa: E402
from MAP_System.scripts.validate_protocol import (  # noqa: E402
    evaluate_protocol,
    maybe_set_halt as protocol_maybe_set_halt,
)


NOW = datetime(2026, 7, 15, 13, 0, tzinfo=timezone.utc)


def write_policy(path: Path, *, enabled_until: str | None, scopes: list[str], granted_by: str | None = "bigboss") -> None:
    rendered_until = "null" if enabled_until is None else enabled_until
    rendered_granted = "null" if granted_by is None else granted_by
    rendered_scopes = "[" + ", ".join(scopes) + "]"
    path.write_text(
        "\n".join(
            [
                "runtime_policy:",
                "  halt_authority_window:",
                f"    enabled_until: {rendered_until}",
                f"    granted_by: {rendered_granted}",
                f"    scope: {rendered_scopes}",
                "",
            ]
        ),
        encoding="utf-8",
    )


def latest_summary(event_log: Path) -> dict:
    lines = event_log.read_text(encoding="utf-8").splitlines()
    payload = json.loads(lines[-1])
    return json.loads(payload["summary"])


def test_disabled_window_is_inactive() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        policy = Path(tmp) / "runtime_policy.yaml"
        write_policy(policy, enabled_until=None, scopes=[])

        status = halt_authority_window_status("layer1", runtime_policy_path=policy, now=NOW)
        assert status["active"] is False
        assert status["reason"] == "disabled"


def test_inactive_window_preserves_telemetry_only_and_logs_would_halt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        policy = root / "runtime_policy.yaml"
        halt_path = root / "halt-state.json"
        event_log = root / "events.jsonl"
        write_policy(policy, enabled_until=None, scopes=[])

        halt_id = layer1_maybe_set_halt(
            {"overall_pass": False, "failing": ["validate_task_graph"]},
            target="TASK-201",
            halt_path=str(halt_path),
            runtime_policy_path=str(policy),
            event_log_path=str(event_log),
            now=NOW,
        )

        assert halt_id is None
        assert not halt_path.exists()
        summary = latest_summary(event_log)
        assert summary["decision"] == "would_halt"
        assert summary["window_active"] is False
        assert summary["adjudication"] == "pending"


def test_active_layer1_window_writes_operator_clearable_halt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        policy = root / "runtime_policy.yaml"
        halt_path = root / "halt-state.json"
        event_log = root / "events.jsonl"
        write_policy(policy, enabled_until="2026-07-16T00:00:00Z", scopes=["layer1"])

        halt_id = layer1_maybe_set_halt(
            {"overall_pass": False, "failing": ["validate_events"]},
            target="TASK-201",
            halt_path=str(halt_path),
            runtime_policy_path=str(policy),
            event_log_path=str(event_log),
            now=NOW,
        )

        assert halt_id is not None
        record = load_halt_state(halt_path)
        assert record["state"] == "repair_only"
        assert record["target"] == "TASK-201"
        assert record["clear_requires"] == "operator"
        summary = latest_summary(event_log)
        assert summary["decision"] == "halt_set"
        assert summary["effective_severity"] == "BLOCKING"
        assert summary["adjudication"] == "pending"


def test_expired_or_scope_mismatched_windows_do_not_halt() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        expired = root / "expired.yaml"
        protocol_only = root / "protocol-only.yaml"
        write_policy(expired, enabled_until="2026-07-15T12:59:59Z", scopes=["layer1"])
        write_policy(protocol_only, enabled_until="2026-07-16T00:00:00Z", scopes=["protocol"])

        for policy in (expired, protocol_only):
            halt_path = root / f"{policy.stem}.halt.json"
            halt_id = layer1_maybe_set_halt(
                {"overall_pass": False, "failing": ["validate_events"]},
                halt_path=str(halt_path),
                runtime_policy_path=str(policy),
                now=NOW,
            )
            assert halt_id is None
            assert not halt_path.exists()


def test_active_protocol_window_writes_halt_for_protocol_violation() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        policy = root / "runtime_policy.yaml"
        halt_path = root / "halt-state.json"
        event_log = root / "events.jsonl"
        write_policy(policy, enabled_until="2026-07-16T00:00:00Z", scopes=["protocol"])
        finding = evaluate_protocol("!HALT bad-token")
        assert finding["adjudication"] == "pending"

        halt_id = protocol_maybe_set_halt(
            finding,
            target="TASK-201",
            halt_path=str(halt_path),
            runtime_policy_path=str(policy),
            event_log_path=str(event_log),
            now=NOW,
        )

        assert halt_id is not None
        record = load_halt_state(halt_path)
        assert record["state"] == "repair_only"
        assert record["clear_requires"] == "operator"
        summary = latest_summary(event_log)
        assert summary["validator_scope"] == "protocol"
        assert summary["decision"] == "halt_set"
        assert summary["adjudication"] == "pending"


def main() -> int:
    tests = [
        test_disabled_window_is_inactive,
        test_inactive_window_preserves_telemetry_only_and_logs_would_halt,
        test_active_layer1_window_writes_operator_clearable_halt,
        test_expired_or_scope_mismatched_windows_do_not_halt,
        test_active_protocol_window_writes_halt_for_protocol_violation,
    ]
    for test in tests:
        test()
        print(f"PASS {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
