#!/usr/bin/env python3
"""Promote HPOM-complete tasks to READY."""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "map.db"
EXPORTER = ROOT / "migration" / "export_to_files.py"

HPOM_JSON_FIELDS = (
    "objective",
    "required_context",
    "files_in_scope",
    "forbidden_changes",
    "acceptance_criteria",
    "expected_artifacts",
    "reviewer_role",
    "risk",
)

SQLITE_FIELD_MAP = {
    "objective": "description",
    "files_in_scope": "output_paths",
    "acceptance_criteria": "acceptance_criteria",
}


@dataclass(frozen=True)
class ValidationResult:
    task_id: str
    missing: tuple[str, ...]

    @property
    def ok(self) -> bool:
        return not self.missing


class PromoteError(RuntimeError):
    pass


def connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def load_task_json(root: Path, task_id: str) -> dict[str, Any]:
    path = root / "tasks" / f"{task_id}.json"
    if not path.exists():
        raise PromoteError(f"{task_id}: missing task JSON at {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_sqlite_task(conn: sqlite3.Connection, task_id: str) -> dict[str, Any]:
    row = conn.execute(
        """
        SELECT task_id, title, description, task_type, role, status, owner,
               required_agent, claimed_by
        FROM tasks
        WHERE task_id = ?
        """,
        (task_id,),
    ).fetchone()
    if row is None:
        raise PromoteError(f"unknown task: {task_id}")
    payload = dict(row)
    payload["output_paths"] = [
        item["path"]
        for item in conn.execute(
            "SELECT path FROM task_output_paths WHERE task_id = ? ORDER BY path",
            (task_id,),
        )
    ]
    payload["acceptance_criteria"] = [
        item["criterion"]
        for item in conn.execute(
            "SELECT criterion FROM task_acceptance_criteria WHERE task_id = ? ORDER BY id",
            (task_id,),
        )
    ]
    return payload


def validate_hpom_contract(task_id: str, sqlite_task: dict[str, Any], task_json: dict[str, Any]) -> ValidationResult:
    missing: list[str] = []

    for hpom_field in HPOM_JSON_FIELDS:
        if not non_empty(task_json.get(hpom_field)):
            missing.append(f"json.{hpom_field}")

    for hpom_field, sqlite_field in SQLITE_FIELD_MAP.items():
        if not non_empty(sqlite_task.get(sqlite_field)):
            missing.append(f"sqlite.{hpom_field}")

    return ValidationResult(task_id=task_id, missing=tuple(missing))


def sync_files(db_path: Path, root: Path) -> None:
    cmd = [sys.executable, str(EXPORTER), "--db", str(db_path)]
    if root != ROOT:
        cmd.extend(["--output-dir", str(root)])
    subprocess.run(cmd, cwd=ROOT.parent, check=True)


def promote_task(task_id: str, *, db_path: Path, root: Path, sync: bool = True) -> ValidationResult:
    with connect(db_path) as conn:
        sqlite_task = load_sqlite_task(conn, task_id)
        if sqlite_task.get("status") == "CONFLICT":
            raise PromoteError(
                f"{task_id}: CONFLICT status — resolve the conflict before promoting to READY"
            )
        task_json = load_task_json(root, task_id)
        result = validate_hpom_contract(task_id, sqlite_task, task_json)
        if not result.ok:
            return result
        conn.execute(
            """
            UPDATE tasks
            SET status = 'READY',
                claimed_by = NULL,
                lease_expires_at = NULL,
                heartbeat_at = NULL,
                updated_at = datetime('now')
            WHERE task_id = ?
            """,
            (task_id,),
        )
    if sync:
        sync_files(db_path, root)
    return result


def audit_ready_tasks(*, db_path: Path, root: Path) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    with connect(db_path) as conn:
        task_ids = [
            row["task_id"]
            for row in conn.execute("SELECT task_id FROM tasks WHERE status = 'READY' ORDER BY task_id")
        ]
        for task_id in task_ids:
            sqlite_task = load_sqlite_task(conn, task_id)
            task_json = load_task_json(root, task_id)
            results.append(validate_hpom_contract(task_id, sqlite_task, task_json))
    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--task-id")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--no-sync", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    db_path = args.db.resolve()
    try:
        if args.audit:
            results = audit_ready_tasks(db_path=db_path, root=root)
            failed = [result for result in results if not result.ok]
            for result in results:
                status = "PASS" if result.ok else "FAIL"
                detail = "" if result.ok else " missing=" + ",".join(result.missing)
                print(f"{status} {result.task_id}{detail}")
            return 1 if failed else 0

        if not args.task_id:
            print("error: --task-id is required unless --audit is used", file=sys.stderr)
            return 2

        result = promote_task(args.task_id, db_path=db_path, root=root, sync=not args.no_sync)
        if not result.ok:
            print(f"error: {result.task_id} missing fields: {', '.join(result.missing)}", file=sys.stderr)
            return 1
        print(json.dumps({"task_id": result.task_id, "status": "READY"}, separators=(",", ":")))
        return 0
    except (sqlite3.Error, json.JSONDecodeError, OSError, subprocess.CalledProcessError, PromoteError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
