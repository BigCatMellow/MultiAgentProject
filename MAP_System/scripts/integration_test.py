#!/usr/bin/env python3
"""Integration test: full agent_loop claim cycle against a temp DB."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_PYTHON = ROOT / ".venv" / "bin" / "python"
if VENV_PYTHON.exists() and Path(sys.executable) != VENV_PYTHON:
    os.execv(str(VENV_PYTHON), [str(VENV_PYTHON), *sys.argv])

SCHEMA = ROOT / "migration" / "schema.sql"
AGENT_LOOP = ROOT / "scripts" / "agent_loop.py"
EXPORTER = ROOT / "migration" / "export_to_files.py"
PYTHON = VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)

PASS = 0
FAIL = 0


def check(label: str, cond: bool, detail: str = "") -> None:
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS: {label}")
    else:
        FAIL += 1
        print(f"FAIL: {label}" + (f" — {detail}" if detail else ""))


def create_temp_db(tmp: Path) -> Path:
    db = tmp / "test.db"
    conn = sqlite3.connect(db)
    conn.executescript(SCHEMA.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO agents (agent_id, label, agent_type, status) VALUES (?,?,?,?)",
        ("test-agent", "Test Agent", "worker", "available"),
    )
    conn.execute(
        """INSERT INTO tasks
           (task_id, project_id, title, description, task_type, role, status,
            priority, attempt, max_attempts, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,datetime('now'),datetime('now'))""",
        ("TASK-IT-01", "TEST-PROJECT", "Integration test task",
         "Verify end-to-end claim cycle", "implementation", "implementer",
         "READY", 1, 0, 3),
    )
    conn.execute(
        "INSERT INTO task_acceptance_criteria (task_id, criterion) VALUES (?, ?)",
        ("TASK-IT-01", "handler submits task"),
    )
    conn.commit()
    conn.close()
    return db


def build_handler(tmp: Path) -> str:
    marker = tmp / "handler_ran.json"
    script = tmp / "handler.py"
    script.write_text(
        f"import json, sys\n"
        f"from pathlib import Path\n"
        f"task_id = sys.argv[1] if len(sys.argv) > 1 else 'unknown'\n"
        f"Path({str(marker)!r}).write_text(json.dumps({{'task_id': task_id}}))\n",
        encoding="utf-8",
    )
    return f"{str(PYTHON)} {str(script)} {{task_id}}"


def run_agent_loop(db: Path, handler_cmd: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            str(PYTHON), str(AGENT_LOOP),
            "--agent-id", "test-agent",
            "--db", str(db),
            "--once",
            "--handler", handler_cmd,
            "--heartbeat-interval", "0.5",
            "--lease-seconds", "60",
            "--no-export-after-submit",
        ],
        cwd=ROOT.parent,
        capture_output=True,
        text=True,
    )


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="map_integration_"))
    try:
        db = create_temp_db(tmp)
        handler_cmd = build_handler(tmp)

        result = run_agent_loop(db, handler_cmd)

        check("agent_loop exited 0", result.returncode == 0,
              f"rc={result.returncode}\nstdout={result.stdout}\nstderr={result.stderr}")
        check("claimed in stdout", "claimed task_id=TASK-IT-01" in result.stdout, result.stdout)
        check("submitted in stdout", "submitted task_id=TASK-IT-01" in result.stdout, result.stdout)

        marker = tmp / "handler_ran.json"
        check("handler executed", marker.exists(), "marker file not found")
        if marker.exists():
            data = json.loads(marker.read_text())
            check("handler received correct task_id", data.get("task_id") == "TASK-IT-01",
                  f"got {data}")

        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT status, claimed_by, lease_expires_at FROM tasks WHERE task_id='TASK-IT-01'"
        ).fetchone()
        conn.close()
        check("task status=SUBMITTED in SQLite", row and row[0] == "SUBMITTED", f"row={row}")
        check("claimed_by cleared", row and row[1] is None, f"claimed_by={row[1] if row else 'N/A'}")
        check("lease cleared", row and row[2] is None, f"lease={row[2] if row else 'N/A'}")

        # Export: use --output-dir to isolate output from real project files
        export_dir = tmp / "export"
        export_result = subprocess.run(
            [str(PYTHON), str(EXPORTER), "--db", str(db), "--output-dir", str(export_dir)],
            cwd=ROOT.parent,
            capture_output=True,
            text=True,
        )
        check("exporter exited 0", export_result.returncode == 0, export_result.stderr)

        task_file = export_dir / "tasks" / "TASK-IT-01.json"
        check("task file exported", task_file.exists())
        if task_file.exists():
            exported = json.loads(task_file.read_text())
            check("exported status=SUBMITTED", exported.get("status") == "SUBMITTED",
                  f"status={exported.get('status')}")

    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    total = PASS + FAIL
    print(f"\n{PASS}/{total} passed" + (" — ALL PASS" if FAIL == 0 else f" — {FAIL} FAILED"))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
