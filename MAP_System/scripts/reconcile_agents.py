#!/usr/bin/env python3
"""Compare durable MAP agent status with live hcom agent JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_STATUS = ROOT / "agents" / "status.json"


def load_durable(path: Path) -> dict[str, str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        name: info.get("status", "unknown")
        for name, info in payload.get("agents", {}).items()
    }


def load_hcom(path: Path | None) -> dict[str, str] | None:
    if path is None:
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        item["name"]: item.get("status", "unknown")
        for item in payload
        if item.get("name")
    }


def reconcile(durable: dict[str, str], live: dict[str, str] | None) -> dict[str, Any]:
    durable_available = {name for name, status in durable.items() if status == "available"}
    if live is None:
        return {
            "durable_available_count": len(durable_available),
            "hcom_input_provided": False,
            "live_count": None,
            "durable_available_not_live": [],
            "live_not_registered": [],
            "live_registered": [],
        }
    live_active = set(live)
    return {
        "durable_available_count": len(durable_available),
        "hcom_input_provided": True,
        "live_count": len(live_active),
        "durable_available_not_live": sorted(durable_available - live_active),
        "live_not_registered": sorted(live_active - set(durable)),
        "live_registered": sorted(live_active & set(durable)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status-file", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--hcom-json", type=Path, help="File containing `hcom list --json` output")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = reconcile(load_durable(args.status_file), load_hcom(args.hcom_json))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Durable available agents: {report['durable_available_count']}")
        if report["hcom_input_provided"]:
            print(f"Live hcom agents: {report['live_count']}")
        else:
            print("Live hcom agents: not checked (--hcom-json not provided)")
            print("Capture live state first: hcom list --json > /tmp/live-hcom.json")
        print("Durable available but not live:")
        for name in report["durable_available_not_live"]:
            print(f"- {name}")
        print("Live but not registered:")
        for name in report["live_not_registered"]:
            print(f"- {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
