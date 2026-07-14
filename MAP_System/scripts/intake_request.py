#!/usr/bin/env python3
"""Draft a MAP/HPOM dispatch packet for an operator request."""

from __future__ import annotations

import argparse
import json
import re


def classify(text: str) -> dict[str, object]:
    lowered = text.lower()
    if re.search(r"\b(push|commit|sync|release|publish|github)\b", lowered):
        return {
            "worker_fit": "codex",
            "risk": "repo_global",
            "risk_class": "PROCESS",
            "needs_task": "yes",
            "task_type": "implementation",
            "task_tier": "core",
            "local_lane": "none",
            "gap_score": "medium",
            "needs_approval": "yes",
            "approval_reason": "repo-global or publication action",
            "decomposition_required": "yes",
            "reviewer": "claude",
            "note": "Requires a Git operation lock and explicit owner before repository-global action.",
            "suggested_output_paths": ["MAP_System/artifacts/planning/[task-specific].md"],
            "acceptance_criteria_stub": [
                "Git operation lock or documented approval gate is used before repo-global action.",
                "Independent review or release checklist covers changed paths.",
            ],
        }
    if re.search(r"\b(review|audit|report|summarize|analy[sz]e)\b", lowered):
        return {
            "worker_fit": "claude_or_codex",
            "risk": "medium",
            "risk_class": "KNOWLEDGE",
            "needs_task": "yes",
            "task_type": "audit",
            "task_tier": "core",
            "local_lane": "summary_draft",
            "gap_score": "medium",
            "needs_approval": "no",
            "approval_reason": "none",
            "decomposition_required": "maybe",
            "reviewer": "other_core_agent",
            "note": "Assign one owner; other agent should support or review.",
            "suggested_output_paths": ["MAP_System/artifacts/audits/[topic].md"],
            "acceptance_criteria_stub": [
                "Audit names input paths and evidence used.",
                "Findings distinguish blocking issues from recommendations.",
            ],
        }
    if re.search(r"\b(write|edit|fix|implement|build|code)\b", lowered):
        return {
            "worker_fit": "codex",
            "risk": "file_edit",
            "risk_class": "PROCESS",
            "needs_task": "yes",
            "task_type": "implementation",
            "task_tier": "core",
            "local_lane": "validator_or_diff_draft",
            "gap_score": "medium",
            "needs_approval": "maybe",
            "approval_reason": "depends on output paths and destructive-action scope",
            "decomposition_required": "maybe",
            "reviewer": "claude",
            "note": "Claim or create a task before substantive edits.",
            "suggested_output_paths": ["[explicit target paths required before claim]"],
            "acceptance_criteria_stub": [
                "Named output paths are registered before edits.",
                "Focused verification command or review artifact exists.",
            ],
        }
    return {
        "worker_fit": "shaper",
        "risk": "unclear",
        "risk_class": "KNOWLEDGE",
        "needs_task": "maybe",
        "task_type": "planning",
        "task_tier": "shaping",
        "local_lane": "none",
        "gap_score": "high",
        "needs_approval": "maybe",
        "approval_reason": "intent, output paths, and acceptance criteria are underspecified",
        "decomposition_required": "yes",
        "reviewer": "tbd",
        "note": "Clarify acceptance criteria before execution.",
        "suggested_output_paths": ["MAP_System/artifacts/planning/[shaping-note].md"],
        "acceptance_criteria_stub": [
            "Request is converted into clear task scope or explicit operator question.",
            "Output paths and acceptance criteria are named before implementation.",
        ],
    }


def dispatch_packet(text: str, owner: str = "") -> dict[str, object]:
    classification = classify(text)
    packet: dict[str, object] = {
        "request": text,
        "owner": owner or "command-center",
        "entrypoint": "command-center-intake",
        "status": "dispatch_draft",
        "direct_message_policy": (
            "Broad operator instructions should be repackaged into this packet "
            "before agents treat them as task authority."
        ),
        "classification": classification,
        "decomposer_contract": {
            "required_fields": [
                "task_type",
                "subtasks",
                "dependencies",
                "output_paths",
                "acceptance_criteria",
                "risk_class",
                "approval_gates",
                "routing_lane",
                "rollback_expectation",
            ],
            "subtasks": [
                {
                    "title": "shape-request",
                    "depends_on": [],
                    "output_paths": classification["suggested_output_paths"],
                    "acceptance_criteria": classification["acceptance_criteria_stub"],
                    "routing_lane": classification["task_tier"],
                }
            ],
        },
    }
    return packet


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    parser.add_argument("--owner", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    packet = dispatch_packet(args.request, owner=args.owner)
    result = dict(packet["classification"])
    if args.owner:
        result["owner"] = args.owner
    result["hcom_inform"] = (
        f"Intake: worker_fit={result['worker_fit']} risk={result['risk']} "
        f"needs_task={result['needs_task']} task_tier={result['task_tier']} "
        f"gap_score={result['gap_score']} reviewer={result['reviewer']} "
        f"note={result['note']}"
    )
    if args.json:
        packet["hcom_inform"] = result["hcom_inform"]
        print(json.dumps(packet, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
