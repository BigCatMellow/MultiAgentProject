#!/usr/bin/env python3
"""Command-center intake wrapper (TASK-167, gap-plan increment 1).

Gives operator intent one mechanical place to become a structured dispatch
packet before an agent treats it as task authority, per
ORCHESTRATION_ENTRYPOINT_SYSTEM.md's Direct Message Policy. This wrapper
does not replace hcom or alter live agent messaging -- direct
operator-to-agent messages remain allowed for attention/live control per
that policy's stated exceptions. It composes three existing pieces rather
than reimplementing any of them:

1. scripts/intake_request.py's dispatch_packet() -- classification logic.
2. A canonical event record of the resulting packet.
3. graph/runner.py's route computation, printed so the operator/agent sees
   what happens next without a second lookup.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.intake_request import dispatch_packet  # noqa: E402
from MAP_System.scripts.validate_protocol import evaluate_protocol  # noqa: E402

DEFAULT_EVENT_LOG = ROOT / "events" / "events.jsonl"
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
RUNNER_PYTHON = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable


class IntakeWrapperError(RuntimeError):
    """Raised when the wrapper's own hcom-shaped output fails protocol validation."""


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append_intake_event(
    packet: dict,
    task_id: str = "TASK-167",
    event_log: Path = DEFAULT_EVENT_LOG,
) -> dict:
    """Records the dispatch packet as a canonical event -- this is the
    mechanical part of "operator intent enters once, is shaped once."
    Uses PROGRESS (canonical type) with the packet's key fields in the
    summary/artifact-free structured form, per the same pattern
    map-kill-switch-spec.md and map-cost-governance-spec.md already use
    for not-yet-schema-extended event types.
    """
    classification = packet["classification"]
    event = {
        "created_at": _now_iso(),
        "type": "PROGRESS",
        "task_id": task_id,
        "sender": "command-center-intake",
        "summary": (
            f"Intake packet: task_type={classification['task_type']} "
            f"risk_class={classification['risk_class']} gap_score={classification['gap_score']} "
            f"owner={packet['owner']} worker_fit={classification['worker_fit']} "
            f"needs_approval={classification['needs_approval']}"
        ),
        "artifact_paths": [],
        "actor": "command-center-intake",
        "action": "intake",
        "target": packet["owner"],
    }
    with open(event_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")
    return event


def validate_wrapper_output(hcom_inform: str) -> dict:
    """The wrapper's own hcom-shaped output (the `hcom_inform` summary
    line intake_request.py already produces) must itself pass protocol
    validation -- the wrapper should not be the one thing in the chain
    that's exempt from the checks it exists to route work through.
    """
    finding = evaluate_protocol(hcom_inform)
    if not finding["passed"]:
        raise IntakeWrapperError(
            f"wrapper's own hcom_inform output failed protocol validation: {finding['reasons']}"
        )
    return finding


def post_hcom_inform(
    hcom_inform: str,
    recipients: list[str],
    *,
    sender_name: str,
    runner=subprocess.run,
) -> dict | None:
    """Post the validated intake packet to hcom as a visible inform message.

    This is intentionally optional so tests, dry-runs, and urgent live-control
    paths can use the same intake classifier without writing to hcom.
    """
    if not recipients:
        return None
    result = runner(
        ["hcom", "send", *recipients, "--intent", "inform", "--name", sender_name, "--", hcom_inform],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    return {
        "recipients": recipients,
        "returncode": result.returncode,
        "stdout": (result.stdout or "").strip(),
        "stderr": (result.stderr or "").strip(),
    }


def get_next_route() -> dict:
    result = subprocess.run(
        [RUNNER_PYTHON, str(ROOT / "graph" / "runner.py"), "--pretty"],
        cwd=REPO, text=True, capture_output=True, check=False,
    )
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise IntakeWrapperError(f"runner did not emit valid JSON: {exc}") from exc


def run_intake(
    text: str,
    owner: str = "",
    task_id: str = "TASK-167",
    event_log: Path = DEFAULT_EVENT_LOG,
    record_event: bool = True,
    hcom_inform_to: list[str] | None = None,
    hcom_name: str = "command-center-intake",
    hcom_runner=subprocess.run,
) -> dict:
    packet = dispatch_packet(text, owner=owner)
    classification = packet["classification"]
    hcom_inform = (
        f"Intake: worker_fit={classification['worker_fit']} risk={classification['risk']} "
        f"needs_task={classification['needs_task']} task_tier={classification['task_tier']} "
        f"gap_score={classification['gap_score']} reviewer={classification['reviewer']} "
        f"note={classification['note']}"
    )
    validate_wrapper_output(hcom_inform)

    hcom_post = post_hcom_inform(
        hcom_inform,
        hcom_inform_to or [],
        sender_name=hcom_name,
        runner=hcom_runner,
    )

    event = None
    if record_event:
        event = append_intake_event(packet, task_id=task_id, event_log=event_log)

    route = get_next_route()
    return {
        "packet": packet,
        "hcom_inform": hcom_inform,
        "hcom_post": hcom_post,
        "event": event,
        "next_route": route.get("next_route"),
        "recommended_action": route.get("recommended_action"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", nargs="?", help="Operator intent text; reads stdin if omitted")
    parser.add_argument("--owner", default="")
    parser.add_argument("--task-id", default="TASK-167")
    parser.add_argument("--no-event", action="store_true", help="Skip appending the intake event (dry run)")
    parser.add_argument(
        "--hcom-inform-to",
        action="append",
        default=[],
        metavar="RECIPIENT",
        help="Post the validated intake packet as hcom --intent inform to this recipient; repeat for multiple recipients",
    )
    parser.add_argument("--hcom-name", default="command-center-intake", help="hcom --name value for --hcom-inform-to")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    text = args.text if args.text is not None else sys.stdin.read().strip()
    if not text:
        print("No operator intent text provided (arg or stdin).", file=sys.stderr)
        return 2

    result = run_intake(
        text,
        owner=args.owner,
        task_id=args.task_id,
        record_event=not args.no_event,
        hcom_inform_to=args.hcom_inform_to,
        hcom_name=args.hcom_name,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["hcom_inform"])
        print(f"next_route: {result['next_route']}")
        print(f"recommended_action: {result['recommended_action']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
