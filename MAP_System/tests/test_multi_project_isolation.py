#!/usr/bin/env python3
"""Multi-project isolation regression tests (taxonomy audit missing test #6, TASK-192).

Anchored on `artifacts/audits/map-multi-project-readiness.md`'s boundaries:
root MAP_System state is MAP-global; Pathwell/ProjectUpdater-class projects
keep project-local tasks/events, and "project-local task operations should
use the project-local scripts/database." Where that promise is mechanical
(separate DB files, project_id inheritance), these tests verify it — the
single-project check runs against the REAL root map.db, so a foreign
project's records leaking into root state fails the suite. Where the promise
is prose only, the test is skipped-with-reason naming the missing mechanism.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "migration" / "schema.sql"

if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from MAP_System.db.claims import claim_task


def load_map_task():
    script = ROOT / "scripts" / "map_task.py"
    spec = importlib.util.spec_from_file_location("map_task", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


map_task = load_map_task()


class SkipTest(Exception):
    """Raised by a test whose isolation mechanism does not exist yet."""


def init_project_db(path: Path, project_id: str, task_id: str) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES "
            "('test-owner', 'Test Owner', 'core', 'available'), "
            "('test-agent', 'Test Agent', 'core', 'available')"
        )
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status,
               owner, attempt, max_attempts)
            VALUES (?, ?, 'Isolated task', 'desc', 'implementation', 'worker',
                    'READY', 'test-owner', 0, 3)
            """,
            (task_id, project_id),
        )
        conn.execute(
            "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES (?, 'isolated')",
            (task_id,),
        )
        conn.execute(
            "INSERT INTO task_output_paths (task_id, path) VALUES (?, 'out/isolated.md')",
            (task_id,),
        )


def test_root_map_db_is_single_project():
    """Live isolation check on real state: the root map.db must contain
    exactly one project_id, and the task-graph mirror must declare the same
    one. A Pathwell/ProjectUpdater record leaking into root MAP state makes
    this fail."""
    with sqlite3.connect(ROOT / "map.db") as conn:
        projects = sorted(
            row[0] for row in conn.execute("SELECT DISTINCT project_id FROM tasks")
        )
    assert len(projects) == 1, f"root map.db contains multiple project_ids: {projects}"

    graph = json.loads((ROOT / "workflow" / "task_graph.json").read_text(encoding="utf-8"))
    assert graph.get("project_id") == projects[0], (
        f"task_graph.json project_id {graph.get('project_id')!r} != db {projects[0]!r}"
    )


def test_task_creation_inherits_db_project_id():
    """map_task.py derives project_id from the database it writes to, so task
    creation cannot silently attach a task to a foreign project."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "proj.db"
        init_project_db(db, "PROJ-X", "TASK-ISO-1")
        with sqlite3.connect(db) as conn:
            conn.row_factory = sqlite3.Row
            assert map_task.project_id(conn) == "PROJ-X"


def test_claims_scoped_to_explicit_db():
    """The claims layer operates only on the db_path it is given: claiming a
    task in a project-local database must succeed there and leave root MAP
    state untouched (no such task id exists in root map.db)."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "proj.db"
        init_project_db(db, "PROJ-X", "TASK-ISO-1")
        assert claim_task("TASK-ISO-1", "test-agent", db_path=db) is True
        with sqlite3.connect(db) as conn:
            status = conn.execute(
                "SELECT status, claimed_by FROM tasks WHERE task_id='TASK-ISO-1'"
            ).fetchone()
        assert status == ("IN_PROGRESS", "test-agent")
    with sqlite3.connect(ROOT / "map.db") as conn:
        row = conn.execute(
            "SELECT COUNT(*) FROM tasks WHERE task_id='TASK-ISO-1'"
        ).fetchone()
    assert row[0] == 0, "fixture task id leaked into root map.db"


def test_cross_project_claim_guard_missing():
    """SHOULD pass once a claim-time project guard exists: an agent operating
    under one project must be rejected (or require an explicit override) when
    claiming a task carrying a different project_id.

    Missing mechanism: db/claims.py checks status/lease/attempts/self-review
    only — project_id is never consulted at claim time. Isolation currently
    rests entirely on projects using physically separate database files, per
    map-multi-project-readiness.md ('project-local task operations should use
    the project-local scripts/database'), which is prose, not a gate."""
    raise SkipTest(
        "no claim-time project guard: db/claims.py never consults project_id; "
        "isolation relies on separate per-project database files (prose rule, "
        "map-multi-project-readiness.md)"
    )


def test_mirror_records_carry_no_project_attribution():
    """SHOULD pass once mirrors carry per-record project attribution: a task
    JSON mirror or graph entry claiming a foreign project_id must be
    detectable by validate_task_mirrors/validate_task_graph.

    Missing mechanism: tasks/TASK-*.json mirrors and task_graph.json entries
    carry no per-record project_id field (only the graph's single top-level
    project_id), so a foreign project's record copied into root mirrors is
    indistinguishable from a native one by every current validator."""
    raise SkipTest(
        "no per-record project attribution in mirrors: task JSON/graph "
        "entries omit project_id, so foreign-project records cannot be "
        "detected by current validators"
    )


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = skipped = 0
    for test in tests:
        try:
            test()
        except SkipTest as skip:
            skipped += 1
            print(f"SKIP {test.__name__}: {skip}")
            continue
        passed += 1
        print(f"PASS {test.__name__}")
    print(f"{passed} multi-project isolation tests passed, {skipped} skipped (missing mechanisms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
