#!/usr/bin/env python3
"""Protocol/MATOCP compliance validator (TASK-162, from map-protocol-validator-spec.md).

Checks hcom message SHAPE against AGENTS.md's 6-token MATOCP subset (!ACK,
!LGTM, !ERR, !REQ, !WARN, !NOTE) -- deliberately NOT the fuller 17-token
spec in Guidelines/llm-communication-rules.md, per this task's own spec's
explicit scope decision (that fuller spec is aspirational/future, not the
operative protocol observed in live hcom traffic). This validator never
judges whether the WORK described is correct -- that is
scripts/validate_layer1.py's and the future semantic-judge's job.

Ships with severity capped at DRIFT (telemetry-only, no halt-store write)
by default, per map-validator-halt-state-spec.md's day-one constraint --
until judge/false-positive accuracy data exists, a protocol finding never
blocks dispatch on its own.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(REPO))

from MAP_System.scripts.halt_state import set_halt  # noqa: E402

DEFAULT_SEVERITY_CAP = "DRIFT"
ESCALATABLE_SEVERITIES = ("DRIFT", "BLOCKING", "STRUCTURAL")

MATOCP_TOKENS = {
    "!ACK": re.compile(r"^!ACK(\s+\S+)?$"),
    "!LGTM": re.compile(r"^!LGTM$"),
    "!ERR": re.compile(r'^!ERR\s+\S+\s+reason="[^"]+"'),
    "!REQ": re.compile(r"^!REQ\s+\S+"),
    "!WARN": re.compile(r'^!WARN\s+\S+\s+reason="[^"]+"'),
    "!NOTE": re.compile(r"^!NOTE\s+.{1,200}$", re.DOTALL),
}

REQUEST_FORMAT_MARKERS = ("Issue:", "Options:", "Recommendation:", "Needed:")
VALID_INTENTS = {"request", "inform", "ack"}


def check_matocp_token(text: str) -> dict:
    """If the text is a MATOCP token line, confirm it's well-formed.

    Text that is not a token line at all (plain prose) is not a violation --
    MATOCP tokens are shorthand for routine cases, not mandatory for
    everything.
    """
    stripped = text.strip()
    if not stripped.startswith("!"):
        return {"applicable": False, "violation": False, "reason": "not a token line"}

    token = stripped.split()[0]
    if token not in MATOCP_TOKENS:
        return {
            "applicable": True,
            "violation": True,
            "reason": f"'{token}' is not one of the operative 6 MATOCP tokens (!ACK/!LGTM/!ERR/!REQ/!WARN/!NOTE)",
            "token": token,
        }

    pattern = MATOCP_TOKENS[token]
    if not pattern.match(stripped):
        return {
            "applicable": True,
            "violation": True,
            "reason": f"{token} present but malformed (does not match required shape)",
            "token": token,
        }
    return {"applicable": True, "violation": False, "reason": "well-formed", "token": token}


def check_intent_presence(intent: str | None, required: bool = False) -> dict:
    """Checks hcom --intent presence and validity -- the first protocol
    scope item named in map-protocol-validator-spec.md ("Does the message
    carry a required --intent?") and the exact condition
    map-validator-halt-probe.md's Protocol halt test exercises: "a malformed
    hcom message (missing required --intent on a broadcast request)".

    `required` is the caller's signal that this particular message needed
    an intent (e.g. a broadcast or a --intent request send) -- most hcom
    traffic (informal chat, non-broadcast) does not require one, so absence
    alone is only a violation when the caller asserts it was required.
    """
    if not required:
        if intent is not None and intent not in VALID_INTENTS:
            return {
                "applicable": True,
                "violation": True,
                "reason": f"intent '{intent}' is not one of {sorted(VALID_INTENTS)}",
            }
        return {"applicable": intent is not None, "violation": False, "reason": "intent not required for this message"}

    if not intent:
        return {
            "applicable": True,
            "violation": True,
            "reason": "required --intent is missing",
        }
    if intent not in VALID_INTENTS:
        return {
            "applicable": True,
            "violation": True,
            "reason": f"intent '{intent}' is not one of {sorted(VALID_INTENTS)}",
        }
    return {"applicable": True, "violation": False, "reason": f"intent '{intent}' present and valid"}


def check_request_format(text: str, is_operator_decision_request: bool = False) -> dict:
    """Operator-decision-shaped requests must carry Issue/Options/
    Recommendation/Needed, per ORCHESTRATION_ENTRYPOINT_SYSTEM.md.
    """
    if not is_operator_decision_request:
        return {"applicable": False, "violation": False, "reason": "not flagged as an operator-decision request"}
    missing = [m for m in REQUEST_FORMAT_MARKERS if m not in text]
    if missing:
        return {
            "applicable": True,
            "violation": True,
            "reason": f"operator-decision request missing required parts: {', '.join(missing)}",
        }
    return {"applicable": True, "violation": False, "reason": "all 4 parts present"}


def evaluate_protocol(
    text: str,
    is_operator_decision_request: bool = False,
    intent: str | None = None,
    intent_required: bool = False,
) -> dict:
    token_check = check_matocp_token(text)
    format_check = check_request_format(text, is_operator_decision_request)
    intent_check = check_intent_presence(intent, required=intent_required)

    violations = [c for c in (token_check, format_check, intent_check) if c.get("violation")]
    passed = not violations
    return {
        "passed": passed,
        "token_check": token_check,
        "format_check": format_check,
        "intent_check": intent_check,
        "reasons": [v["reason"] for v in violations],
        # Adjudication is filled in later by a reviewing agent, not this
        # validator -- per map-protocol-validator-spec.md's adjudication
        # table. Default "pending" avoids silently asserting true_positive.
        "adjudication": "pending" if violations else "not_applicable",
    }


def maybe_set_halt(
    finding: dict,
    *,
    severity: str = DEFAULT_SEVERITY_CAP,
    scope: str = "task",
    target: str | None = None,
    set_by: str = "validator-protocol",
    halt_path: str | None = None,
) -> str | None:
    """Write into TASK-159's shared halt store on a BLOCKING/STRUCTURAL
    finding -- NEVER a new halt table, per the reconciled halt-state spec.
    A DRIFT-severity finding (the shipped default) never calls set_halt;
    it is telemetry only.
    """
    if finding["passed"]:
        return None
    if severity not in ESCALATABLE_SEVERITIES:
        raise ValueError(f"unknown severity: {severity}")
    if severity == "DRIFT":
        return None

    state = "halt_all_dispatch" if severity == "STRUCTURAL" else "repair_only"
    halt_scope = "global" if severity == "STRUCTURAL" else scope
    record = set_halt(
        state=state,
        reason="validator_blocking_anomaly",
        set_by=set_by,
        scope=halt_scope,
        target=target if halt_scope != "global" else None,
        path=halt_path,
    )
    return record["halt_id"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", help="Message text to evaluate")
    parser.add_argument("--operator-decision-request", action="store_true")
    parser.add_argument("--intent", choices=sorted(VALID_INTENTS), help="hcom --intent this message was sent with, if any")
    parser.add_argument("--intent-required", action="store_true", help="Flag this message as one that must carry an intent (e.g. a broadcast)")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    finding = evaluate_protocol(
        args.text, args.operator_decision_request,
        intent=args.intent, intent_required=args.intent_required,
    )
    if args.json:
        print(json.dumps(finding, indent=2))
    else:
        print("PASS" if finding["passed"] else "FAIL: " + "; ".join(finding["reasons"]))
    return 0 if finding["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
