#!/usr/bin/env python3
"""Draft a MAP/HPOM intake recommendation for an operator request."""

from __future__ import annotations

import argparse
import json
import re


def classify(text: str) -> dict[str, str]:
    lowered = text.lower()
    if re.search(r"\b(push|commit|sync|release|publish|github)\b", lowered):
        return {
            "worker_fit": "codex",
            "risk": "repo_global",
            "needs_task": "yes",
            "reviewer": "claude",
            "note": "Requires a Git operation lock and explicit owner before repository-global action.",
        }
    if re.search(r"\b(review|audit|report|summarize|analy[sz]e)\b", lowered):
        return {
            "worker_fit": "claude_or_codex",
            "risk": "medium",
            "needs_task": "yes",
            "reviewer": "other_core_agent",
            "note": "Assign one owner; other agent should support or review.",
        }
    if re.search(r"\b(write|edit|fix|implement|build|code)\b", lowered):
        return {
            "worker_fit": "codex",
            "risk": "file_edit",
            "needs_task": "yes",
            "reviewer": "claude",
            "note": "Claim or create a task before substantive edits.",
        }
    return {
        "worker_fit": "shaper",
        "risk": "unclear",
        "needs_task": "maybe",
        "reviewer": "tbd",
        "note": "Clarify acceptance criteria before execution.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request")
    parser.add_argument("--owner", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = classify(args.request)
    if args.owner:
        result["owner"] = args.owner
    result["hcom_inform"] = (
        f"Intake: worker_fit={result['worker_fit']} risk={result['risk']} "
        f"needs_task={result['needs_task']} reviewer={result['reviewer']} "
        f"note={result['note']}"
    )
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
