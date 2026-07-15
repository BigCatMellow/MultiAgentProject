#!/usr/bin/env python3
"""Context/summary drift regression tests (taxonomy audit missing test #5, TASK-192).

Taxonomy #5 names the failure mode "compressed handoff missing blocker or
stale task state." These tests exercise the negative paths of the drift
detectors that exist (a summary/mirror that no longer matches its source must
make the detector FIRE), and record the detector gaps that don't exist as
skipped-with-reason tests naming the missing mechanism — an honest tracked
gap, not a fabricated pass.
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "migration" / "schema.sql"


def load_module(script_name: str):
    script = ROOT / "scripts" / script_name
    spec = importlib.util.spec_from_file_location(script_name[:-3], script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


validate_task_mirrors = load_module("validate_task_mirrors.py")
validate_shared_state = load_module("validate_shared_state.py")


class SkipTest(Exception):
    """Raised by a test whose detector mechanism does not exist yet."""


def init_db(path: Path) -> None:
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT INTO agents (agent_id, label, agent_type, status) VALUES "
            "('test-owner', 'Test Owner', 'core', 'available')"
        )
        conn.execute(
            """
            INSERT INTO tasks
              (task_id, project_id, title, description, task_type, role, status,
               owner, attempt, max_attempts)
            VALUES
              ('TASK-M', 'TEST', 'Mirror task', 'desc', 'implementation',
               'worker', 'IN_PROGRESS', 'test-owner', 0, 3)
            """
        )
        conn.execute(
            "INSERT INTO task_output_paths (task_id, path) VALUES ('TASK-M', 'MAP_System/example.md')"
        )
        conn.execute(
            "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES ('TASK-M', 'mirrors match')"
        )


def mirror_payload() -> dict:
    return {
        "task_id": "TASK-M",
        "title": "Mirror task",
        "task_type": "implementation",
        "role": "worker",
        "status": "IN_PROGRESS",
        "dependencies": [],
        "owner": "test-owner",
        "description": "desc",
        "input_paths": [],
        "output_paths": ["MAP_System/example.md"],
        "acceptance_criteria": ["mirrors match"],
    }


def write_mirrors(root: Path, *, omit_from_graph: bool = False,
                  ghost_task: bool = False) -> None:
    (root / "tasks").mkdir(parents=True)
    (root / "workflow").mkdir(parents=True)
    task = mirror_payload()
    (root / "tasks" / "TASK-M.json").write_text(json.dumps(task, indent=2) + "\n", encoding="utf-8")
    if ghost_task:
        ghost = dict(task, task_id="TASK-GHOST", title="No SQLite row behind this")
        (root / "tasks" / "TASK-GHOST.json").write_text(json.dumps(ghost, indent=2) + "\n", encoding="utf-8")
    graph_tasks = [] if omit_from_graph else [
        {key: task[key] for key in [
            "task_id", "title", "task_type", "role", "status", "dependencies",
            "owner", "output_paths", "acceptance_criteria"]}
    ]
    (root / "workflow" / "task_graph.json").write_text(
        json.dumps({"project_id": "TEST", "tasks": graph_tasks, "approval_gates": []},
                   indent=2) + "\n",
        encoding="utf-8",
    )


def test_stale_graph_summary_missing_task_fires():
    """A task present in canonical SQLite but absent from the task-graph
    summary mirror is stale task state — the detector must fire."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)
        write_mirrors(out, omit_from_graph=True)
        errors = validate_task_mirrors.validate(db, out)
        assert any("task_graph.json missing TASK-M" in e for e in errors), errors


def test_ghost_mirror_without_source_fires():
    """A mirror file with no canonical row behind it is a summary that has
    drifted from a now-absent source — the detector must fire."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        db = base / "map.db"
        out = base / "out"
        init_db(db)
        write_mirrors(out, ghost_task=True)
        errors = validate_task_mirrors.validate(db, out)
        assert any("task file mirror has no SQLite task: TASK-GHOST" in e
                   for e in errors), errors


def shared_file(tmp: Path, header: str, body: str = "content\n") -> Path:
    path = tmp / "doc.md"
    path.write_text(header + "\n# Doc\n\n" + body, encoding="utf-8")
    return path


FULL_HEADER = """<!-- hpom: file: shared/doc.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: {status} -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: TASK-192 test fixture -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: {superseded_by} -->"""


def test_stale_and_superseded_statuses_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        for status in ("STALE", "SUPERSEDED", "NEEDS_REVIEW"):
            path = shared_file(base, FULL_HEADER.format(status=status, superseded_by="NONE"))
            issues = validate_shared_state.check_file(path)
            assert any(issue.startswith(f"STATUS_{status}") for issue in issues), (status, issues)
        # clean CURRENT file produces no issues
        path = shared_file(base, FULL_HEADER.format(status="CURRENT", superseded_by="NONE"))
        assert validate_shared_state.check_file(path) == []


def test_missing_metadata_and_fields_flagged():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        path = shared_file(base, "")  # no hpom header at all
        issues = validate_shared_state.check_file(path)
        assert any("MISSING_METADATA" in issue for issue in issues), issues
        partial = "<!-- hpom: file: shared/doc.md -->\n<!-- hpom: status: CURRENT -->"
        path = shared_file(base, partial)
        issues = validate_shared_state.check_file(path)
        assert any("MISSING_FIELD: last_verified" in issue for issue in issues), issues


def test_summary_content_drift_detector_missing():
    """SHOULD pass once a content-drift detector exists: edit a source doc
    after its summary's last_verified date and the detector flags the summary.

    Missing mechanism: validate_shared_state.py reads only the self-declared
    hpom header (status/last_verified); nothing compares a summary's content
    (or a checksum/mtime linkage) against the source document it summarizes,
    so a source edited after summarization drifts silently until a human
    re-marks the header."""
    raise SkipTest(
        "no content-drift detector: validate_shared_state.py checks "
        "self-declared hpom metadata only; no source-to-summary content/"
        "checksum comparison mechanism exists"
    )


def test_handoff_missing_blocker_detector_missing():
    """SHOULD pass once a handoff cross-checker exists: a context packet or
    handoff claiming 'no blockers' for a task whose canonical status is
    BLOCKED must be flagged.

    Missing mechanism: validate_context_packets.py checks template fragments
    and unfilled placeholders only; no validator cross-references packet/
    handoff claims (blockers, task status) against canonical task state in
    map.db — taxonomy #5's 'compressed handoff missing blocker' case has no
    detector."""
    raise SkipTest(
        "no handoff cross-checker: validate_context_packets.py validates "
        "template shape/placeholders only; packet claims are never compared "
        "against canonical task state"
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
    print(f"{passed} context-drift tests passed, {skipped} skipped (missing mechanisms)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
