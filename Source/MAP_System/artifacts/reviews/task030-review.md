# Review - TASK-030: Multi-gate handling in LangGraph runner

Reviewer: codex  
Date: 2026-06-23  
Verdict: CHANGES_REQUESTED

## Findings

| ID | Severity | Area | Finding |
|---|---|---|---|
| R-01 | REQUIRED | `MAP_System/graph/runner.py` | `--reject <gate_id>` reports the requested gate as rejected, but the gate is stored as `approved` in SQLite during a multi-gate resume sequence. This violates the acceptance criterion that `--approve/--reject` applies the specified gate decision. |

## Verification

Passing:

```bash
python3 -m py_compile MAP_System/graph/runner.py
MAP_System/.venv/bin/python MAP_System/graph/runner.py --pretty
MAP_System/scripts/run_tests.sh
```

Failing targeted multi-gate fixture:

```text
FIRST_RC 0
pending_gates: GATE-A, GATE-B

SECOND_RC 0
processed: {"gate_id": "GATE-A", "decision": "approved"}
next pending gate: GATE-B

THIRD_RC 0
processed as rejected in CLI output:
{"gate_id": "GATE-B", "decision": "rejected"}

SQLite rows:
[("GATE-A", "approved"), ("GATE-B", "approved")]
```

Expected final rows:

```text
[("GATE-A", "approved"), ("GATE-B", "rejected")]
```

## Improvements Checked

Implemented:
- None; this is a review of a Claude-owned submitted task.

Recommended:
- Add a targeted regression fixture for approve-then-reject across two pending gates. It directly covers the bug and would prevent future false approvals.

Not changed:
- `MAP_System/graph/runner.py` was not edited by the reviewer because it is the submitted output path for another agent's active task.
