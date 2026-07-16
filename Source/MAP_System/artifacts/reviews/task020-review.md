# Review — TASK-020: Autonomous Claim Loop Protocol

Reviewer: codex  
Date: 2026-06-19  
Verdict: APPROVED

## Acceptance Criteria

| Criterion | Result |
|---|---|
| Defines poll-claim-work-heartbeat-submit cycle | PASS |
| Specifies claim race, heartbeat timeout, max attempts, and other failures | PASS |
| Specifies interaction with reconcile.py and runner | PASS |
| Defines safe shutdown protocol | PASS |
| Pseudocode or flowchart illustrates full loop | PASS |

## Notes

The spec is implementation-ready for a future `scripts/agent_loop.py` task. The recommended subprocess handler question is correctly left open for the implementer because it affects safety and process isolation.

No BLOCKER or REQUIRED findings.
