#!/usr/bin/env python3
"""Pre-dispatch policy checker for MAP task assignments.

The checker is deterministic and intentionally conservative around explicit
metadata. Text fallback only catches obvious hard-stop phrases so existing
tasks without TASK-153/TASK-156 metadata do not become silently unroutable.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DEFAULT_DB = ROOT / "map.db"

DECISIONS = {"allow", "require_approval", "reject"}
VALID_TIERS = {0, 1, 2, 3, 4}
VALID_INTENTIONAL_DRAFT_LANES = {
    "repo_scan",
    "json_schema_check",
    "event_digest",
    "validator_log_summary",
    "markdown_cleanup",
    "acceptance_criteria_draft",
}
COMMAND_CENTER_APPROVAL = "command-center"
OWNING_CORE_APPROVAL = "owning-core-agent"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def upper_value(value: Any) -> str:
    return str(value or "").strip().upper()


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return normalize(value) in {"1", "true", "yes", "y", "on"}


def list_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, tuple):
        return [str(item) for item in value]
    return [str(value)]


def task_text(task: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("task_id", "title", "description", "task_type", "role"):
        parts.append(str(task.get(key, "")))
    parts.extend(list_value(task.get("acceptance_criteria")))
    return " ".join(parts).lower()


def contains_any(text: str, needles: tuple[str, ...]) -> bool:
    return any(needle in text for needle in needles)


def infer_worker_tier(candidate_worker: str, worker_tier: int | str | None = None) -> int:
    if worker_tier is not None and str(worker_tier).strip() != "":
        tier = int(worker_tier)
        if tier not in VALID_TIERS:
            raise ValueError(f"unknown worker tier: {worker_tier}")
        return tier

    worker = normalize(candidate_worker)
    if worker in {"command-center", "bigboss", "operator", "human"}:
        return 0
    if "aider" in worker:
        return 4
    if "local" in worker or "ollama" in worker:
        return 3
    if "helper" in worker or worker.startswith("task") and "review" in worker:
        return 2
    return 1


def tier_label(tier: int) -> str:
    labels = {
        0: "tier0_command_center",
        1: "tier1_core_agent",
        2: "tier2_visible_helper",
        3: "tier3_local_assistant",
        4: "tier4_aider_wrapper",
    }
    return labels[tier]


def is_draft_only(task: dict[str, Any], assignment_mode: str | None = None) -> bool:
    lane = normalize(task.get("local_lane"))
    if as_bool(task.get("draft_only")):
        return True
    if normalize(assignment_mode) in {"draft", "helper_draft", "review_draft"}:
        return True
    if lane in VALID_INTENTIONAL_DRAFT_LANES:
        return True
    text = task_text(task)
    return "draft" in text and "final" not in text and "approve" not in text


def is_final_review(task: dict[str, Any]) -> bool:
    if as_bool(task.get("final_review")):
        return True
    if is_draft_only(task):
        return False
    task_type = normalize(task.get("task_type"))
    role = normalize(task.get("role"))
    text = task_text(task)
    return task_type == "review" or role == "reviewer" or contains_any(text, ("final review", "approve task", "approval review"))


def is_final_decision(task: dict[str, Any]) -> bool:
    if as_bool(task.get("final_decision")) or as_bool(task.get("binding_decision")):
        return True
    if is_draft_only(task):
        return False
    task_type = normalize(task.get("task_type"))
    role = normalize(task.get("role"))
    text = task_text(task)
    return task_type == "decision" or role in {"decision_maker", "approver"} or contains_any(text, ("record decision", "final decision", "make binding"))


def is_broad_architecture(task: dict[str, Any]) -> bool:
    if as_bool(task.get("broad_architecture")):
        return True
    task_type = normalize(task.get("task_type"))
    task_tier = normalize(task.get("task_tier"))
    decision_class = upper_value(task.get("decision_class"))
    text = task_text(task)
    return (
        task_type == "architecture"
        or task_tier == "architecture"
        or decision_class == "ARCHITECTURE"
        or contains_any(text, ("broad architecture", "architecture ownership"))
    )


def is_broad_rewrite(task: dict[str, Any]) -> bool:
    if as_bool(task.get("broad_rewrite")):
        return True
    text = task_text(task)
    output_paths = list_value(task.get("output_paths"))
    return len(output_paths) > 5 or contains_any(text, ("broad rewrite", "rewrite across", "multi-file rewrite"))


def is_destructive(task: dict[str, Any]) -> bool:
    if as_bool(task.get("destructive_action")):
        return True
    text = task_text(task)
    return contains_any(
        text,
        (
            "force push",
            "git reset --hard",
            "git clean",
            "delete database",
            "drop table",
            "remove dependency",
            "downgrade dependency",
            "restart service",
            "kill process",
            "--no-verify",
            "hard-to-reverse",
        ),
    )


def requires_shell_or_network(task: dict[str, Any]) -> bool:
    if as_bool(task.get("shell_required")) or as_bool(task.get("network_required")):
        return True
    text = task_text(task)
    return contains_any(
        text,
        (
            "run shell",
            "shell command",
            "subprocess",
            "network call",
            "external-service integration",
            "external service integration",
            "pip install",
            "curl ",
        ),
    )


def mutates_canonical_map(task: dict[str, Any]) -> bool:
    if as_bool(task.get("canonical_map_mutation")):
        return True
    canonical_prefixes = (
        "MAP_System/tasks/",
        "MAP_System/workflow/task_graph.json",
        "MAP_System/workflow/map.db",
        "MAP_System/map.db",
        "MAP_System/events/events.jsonl",
        "MAP_System/shared/",
        "MAP_System/agents/status.json",
    )
    for path in list_value(task.get("output_paths")):
        normalized = path.replace("\\", "/")
        if normalized.startswith(canonical_prefixes):
            return True
    return "canonical map mutation" in task_text(task)


def crosses_trust_boundary(task: dict[str, Any]) -> bool:
    if as_bool(task.get("trust_boundary_crossing")):
        return True
    boundary = normalize(task.get("trust_boundary"))
    if boundary in {"repo", "machine", "network", "external"}:
        return True
    if as_bool(task.get("writes_outside_repo")) or as_bool(task.get("machine_wide_change")):
        return True
    text = task_text(task)
    return contains_any(text, ("new external-service integration", "new external service integration", "write outside the repo", "machine-wide"))


def approval_needed(reason: str) -> str:
    if reason == "REQUIRE_OWNING_CORE_DELEGATION":
        return OWNING_CORE_APPROVAL
    return COMMAND_CENTER_APPROVAL


def evaluate_pre_dispatch(
    task: dict[str, Any],
    candidate_worker: str,
    *,
    worker_tier: int | str | None = None,
    assignment_mode: str | None = None,
    checked_at: str | None = None,
) -> dict[str, Any]:
    """Return allow, require_approval, or reject for a proposed assignment."""
    tier = infer_worker_tier(candidate_worker, worker_tier)
    reject_reasons: list[str] = []
    approval_reasons: list[str] = []
    required_evidence: list[str] = []

    decision_class = upper_value(task.get("decision_class"))
    risk_class = upper_value(task.get("risk_class"))
    risk_severity = upper_value(task.get("risk_severity"))
    task_tier = normalize(task.get("task_tier"))

    final_review = is_final_review(task)
    final_decision = is_final_decision(task)
    broad_architecture = is_broad_architecture(task)
    broad_rewrite = is_broad_rewrite(task)
    destructive = is_destructive(task)
    shell_or_network = requires_shell_or_network(task)
    canonical_mutation = mutates_canonical_map(task)
    trust_boundary = crosses_trust_boundary(task)
    draft_only = is_draft_only(task, assignment_mode)

    if tier == 0:
        return result_record(task, candidate_worker, tier, "allow", ["ALLOW_COMMAND_CENTER"], [], None, checked_at)

    if tier >= 2:
        if final_review:
            reject_reasons.append("REJECT_HELPER_FINAL_REVIEW")
        if final_decision:
            reject_reasons.append("REJECT_HELPER_FINAL_DECISION")
        if broad_architecture and not draft_only:
            reject_reasons.append("REJECT_HELPER_BROAD_ARCHITECTURE")
        if broad_rewrite:
            reject_reasons.append("REJECT_HELPER_BROAD_REWRITE")
        if destructive:
            reject_reasons.append("REJECT_HELPER_DESTRUCTIVE")
        if shell_or_network:
            reject_reasons.append("REJECT_HELPER_SHELL_NETWORK")
        if canonical_mutation:
            reject_reasons.append("REJECT_HELPER_CANONICAL_MUTATION")
        if decision_class in {"AUTHORITY", "POLICY"} and not draft_only:
            reject_reasons.append("REJECT_HELPER_AUTHORITY_POLICY_FINALIZATION")

    if tier >= 3:
        if shell_or_network:
            reject_reasons.append("REJECT_LOCAL_SHELL_NETWORK")
        if canonical_mutation:
            reject_reasons.append("REJECT_LOCAL_CANONICAL_MUTATION")
        if task_tier not in {"mechanical", "bounded", ""} and not draft_only:
            reject_reasons.append("REJECT_LOCAL_NON_DRAFT_TIER")

    if tier == 4 and broad_rewrite:
        reject_reasons.append("REJECT_AIDER_BROAD_SCOPE")

    if tier == 1:
        if as_bool(task.get("requires_operator_approval")):
            approval_reasons.append("REQUIRE_OPERATOR_APPROVAL")
            required_evidence.append("operator approval")
        if destructive:
            approval_reasons.append("REQUIRE_CORE_DESTRUCTIVE_APPROVAL")
            required_evidence.append("operator instruction or approving decision")
        if decision_class in {"AUTHORITY", "POLICY"}:
            approval_reasons.append("REQUIRE_COMMAND_CENTER_DECISION")
            required_evidence.append("command-center approval or DEC record")
        if task_tier == "operator":
            approval_reasons.append("REQUIRE_OPERATOR_TIER_APPROVAL")
            required_evidence.append("Issue/Options/Recommendation/Needed operator response")
        if risk_class == "SECURITY" or risk_severity == "STRUCTURAL":
            approval_reasons.append("REQUIRE_SECURITY_STRUCTURAL_APPROVAL")
            required_evidence.append("risk entry or command-center approval")
        if trust_boundary and not (risk_class or risk_severity):
            approval_reasons.append("REQUIRE_UNKNOWN_TRUST_BOUNDARY_APPROVAL")
            required_evidence.append("risk classification")

    if reject_reasons:
        return result_record(task, candidate_worker, tier, "reject", sorted(set(reject_reasons)), [], None, checked_at)

    if approval_reasons:
        unique_reasons = sorted(set(approval_reasons))
        authority = COMMAND_CENTER_APPROVAL
        return result_record(task, candidate_worker, tier, "require_approval", unique_reasons, sorted(set(required_evidence)), authority, checked_at)

    if tier == 2 and draft_only:
        return result_record(task, candidate_worker, tier, "allow", ["ALLOW_HELPER_DRAFT"], [], None, checked_at)
    if tier == 3 and draft_only:
        lane = normalize(task.get("local_lane"))
        if lane and lane not in VALID_INTENTIONAL_DRAFT_LANES:
            return result_record(task, candidate_worker, tier, "reject", ["REJECT_LOCAL_UNKNOWN_LANE"], [], None, checked_at)
        return result_record(task, candidate_worker, tier, "allow", ["ALLOW_LOCAL_DRAFT_LANE"], [], None, checked_at)

    return result_record(task, candidate_worker, tier, "allow", ["ALLOW_WITHIN_TIER"], [], None, checked_at)


def result_record(
    task: dict[str, Any],
    candidate_worker: str,
    tier: int,
    decision: str,
    reasons: list[str],
    required_evidence: list[str],
    approval_authority: str | None,
    checked_at: str | None,
) -> dict[str, Any]:
    if decision not in DECISIONS:
        raise ValueError(f"unknown decision: {decision}")
    return {
        "task_id": task.get("task_id"),
        "candidate_worker": candidate_worker,
        "worker_tier": tier_label(tier),
        "decision": decision,
        "reasons": reasons,
        "approval_authority": approval_authority,
        "required_evidence": required_evidence,
        "checked_at": checked_at or utc_now(),
    }


def load_task_from_db(task_id: str, db_path: str | Path = DEFAULT_DB) -> dict[str, Any]:
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(
            """
            SELECT task_id, project_id, title, description, task_type, role, status,
                   priority, required_agent, owner, claimed_by, attempt, max_attempts
            FROM tasks
            WHERE task_id = ?
            """,
            (task_id,),
        ).fetchone()
        if row is None:
            raise KeyError(task_id)
        task = dict(row)
        task["output_paths"] = [
            value
            for (value,) in conn.execute(
                "SELECT path FROM task_output_paths WHERE task_id = ? ORDER BY path",
                (task_id,),
            )
        ]
        task["acceptance_criteria"] = [
            value
            for (value,) in conn.execute(
                "SELECT criterion FROM task_acceptance_criteria WHERE task_id = ? ORDER BY id",
                (task_id,),
            )
        ]
        return task


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--task-json", help="Path to a JSON task packet")
    source.add_argument("--task-id", help="Task ID to load from map.db")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="SQLite DB for --task-id")
    parser.add_argument("--candidate-worker", required=True)
    parser.add_argument("--worker-tier", type=int, choices=sorted(VALID_TIERS))
    parser.add_argument("--assignment-mode")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.task_json:
        task = json.loads(Path(args.task_json).read_text(encoding="utf-8"))
    else:
        task = load_task_from_db(args.task_id, args.db)

    result = evaluate_pre_dispatch(
        task,
        args.candidate_worker,
        worker_tier=args.worker_tier,
        assignment_mode=args.assignment_mode,
    )
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"{result['decision']} {' '.join(result['reasons'])}")
    return 0 if result["decision"] == "allow" else 1


if __name__ == "__main__":
    raise SystemExit(main())
