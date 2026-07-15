#!/usr/bin/env python3
"""Declare an agent's work-state (TASK-084 / IDEA-0007 declared-idle protocol).

    declare_standby.py <agent>          -> standby / awaiting_work (queue empty;
                                           RnS check-ins leave you alone)
    declare_standby.py <agent> --back   -> available (working again)
    declare_standby.py <agent> --terminal session_superseded
                                        -> inactive / session_superseded
    declare_standby.py <agent> --terminal disposable_session_ended
                                        -> inactive / disposable_session_ended
                                           (dead on purpose, TASK-186/IDEA-0009;
                                           RnS never probes, resumes, or nudges)

Writes SQLite FIRST (the agents table is the source of truth; status.json is
an exporter mirror -- see SYN-0001), then exports so all views agree.
"""

from __future__ import annotations

import argparse
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "map.db"
EXPORTER = ROOT / "migration" / "export_to_files.py"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("agent", help="agent id, e.g. claude-lab-rose")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--back", action="store_true",
                       help="return to available instead of declaring standby")
    group.add_argument("--terminal",
                       choices=("session_superseded", "disposable_session_ended"),
                       help="mark the session durably dead on purpose "
                            "(inactive/<value>; RnS suppresses probes and nudges, "
                            "TASK-186/IDEA-0009)")
    args = parser.parse_args()

    if args.back:
        status, reason = "available", None
    elif args.terminal:
        status, reason = "inactive", args.terminal
    else:
        status, reason = "standby", "awaiting_work"

    con = sqlite3.connect(DB)
    row = con.execute("SELECT 1 FROM agents WHERE agent_id=?", (args.agent,)).fetchone()
    if row is None:
        print(f"error: unknown agent {args.agent!r} (not in SQLite agents table)",
              file=sys.stderr)
        return 1
    con.execute(
        "UPDATE agents SET status=?, reason=?, resume_after=NULL, "
        "updated_at=CURRENT_TIMESTAMP WHERE agent_id=?",
        (status, reason, args.agent))
    con.commit()
    con.close()

    result = subprocess.run([sys.executable, str(EXPORTER)],
                            capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"warning: SQLite updated but export failed: {result.stderr.strip()}",
              file=sys.stderr)
        return 1

    print(f"{args.agent}: {status}" + (f" ({reason})" if reason else "") +
          " -- SQLite updated, mirrors exported")
    return 0


if __name__ == "__main__":
    sys.exit(main())
