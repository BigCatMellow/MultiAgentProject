# Full-Report Coverage Matrix — 2026-07-02

Task: TASK-082 (claude-lab-rose). Verifies every item in
`artifacts/reports/MAP-system-full-report-2026-07-02.md` against what was
actually done. Peer lane: codex-lab-limo's TASK-081 (tooling closures).

Legend: DONE (evidence cited) | PARTIAL | DEFERRED (with reason) | N/A.

## Findings F1-F9

| Item | Status | Evidence |
|---|---|---|
| F1 Repo canonicality (P0) | DONE | DEC-012; commit `5cb8a61` pushed to origin (TASK-079, operator-authorized); B recloned at `5cb8a61` w/ private Pathwell/Backups restored, chapters diff-identical; drifted copy archived w/ freeze marker; `shared/canonical-repo.md`. |
| F2 Task ID allocation (P0/P1) | DONE | `map_task.py create --task-id auto` under `BEGIN IMMEDIATE` (TASK-065); first real use allocated TASK-082; `test_map_task_auto_id`. |
| F3 Emergence lifecycle (P1) | DONE | `map_emergence.py stale` (TASK-065); all 11 stale root records closed (TASK-075, APPROVED); two full pipelines run to durable artifacts (TASK-078, APPROVED: PROMO-0004→AGENTS.md security second pass, PROMO-0005→notes/release-path-checklist.md); INS-0007 captured and implemented. |
| F4 Operator intake (P1) | DONE | `intake_request.py` (TASK-065), exercised in TASK-065 review; intake-before-edit practiced across TASK-075..082 (every lane task-claimed before work). |
| F5 Approval calibration (P1) | DONE | `shared/approval-calibration.md` (TASK-065); lived: TASK-079 paused exactly at the push gate for direct operator word, everything else ran autonomously. |
| F6 Agent availability (P2) | DONE | `reconcile_agents.py` (TASK-065) + actually run: status.json reconciled 16→6 available with all remaining deltas explainable; identity-kind semantics in `agents/README.md` (TASK-082). |
| F7 Event schema (P2) | DONE | `validate_events.py` warn-mode (TASK-065): 0 errors / 33 expected historical warnings; new events use canonical shape; metrics alias grouping landed in TASK-081 (`test_map_metrics_aliases`). |
| F8 Non-MAP projects (P2/P3) | DONE | Bridging note written: `~/Projects/Onion-workbench/claude-code-comms/COORDINATION_BRIDGE.md`; ChainShovel/PixelAnimator deliberately left alone per report. |
| F9 Create-time self-review shape (P3) | DONE | Warning live at map_task.py:157-161 (verified in TASK-065 review); TASK-081 carries verification. |

## Things To Add 1-7

| Item | Status | Evidence |
|---|---|---|
| 1 Atomic task ID allocator | DONE | See F2. |
| 2 Git operation lock | DONE | `git_operation_lock.py`; used live through TASK-079's commit/push/reconcile. |
| 3 Emergence stale report | DONE | See F3; reports "no findings" post-cleanup. |
| 4 Event validator | DONE | See F7. |
| 5 Agent availability reconcile | DONE | See F6 — built AND run. |
| 6 Intake helper | DONE | See F4. |
| 7 Canonical repo marker | DONE | `shared/canonical-repo.md` + DEC-012. |

## Things To Change 1-5

| Item | Status | Evidence |
|---|---|---|
| 1 Emergence lifecycle habit | DONE | 19 emergence artifacts all in honest terminal or active states; stale report clean; lifecycle close-outs practiced same-day (INS-0006, SYN-0001). |
| 2 Tool-assigned task IDs | DONE | TASK-082 allocated via auto; manual IDs now the exception. |
| 3 Ask at the right gate | DONE | approval-calibration.md + demonstrated (F5). |
| 4 One canonical event shape | DONE | All new events canonical; legacy tolerated with warnings by design. |
| 5 Two agent-state concepts | DONE | agents/README.md identity kinds; hcom = live authority, status.json = durable record. |

## Beyond the report (same period)

- Limit watcher (TASK-080, APPROVED after one rejection cycle): auto-resume
  after usage-limit resets + silent-stop detection — extends F6 into runtime.
- `notes/limit-exhaustion-protocol.md`: limit handling + resume convention.
- `map_task.py rework` (TASK-081): closes the CHANGES_REQUESTED dead-end
  found by TASK-080's rejection — first rejection in system history.
- Generated/shared-file validator handling (TASK-081).
- SYN-0001 "two readers, one truth" — first synthesis record; design rule
  predicting/preventing the next class of failures.
- DEC-013: SYN/EXP types stay active, non-ceremonial.

## Phases

| Phase | Status | Notes |
|---|---|---|
| 0 Safety freeze | DONE | DEC-012 recorded before any git ops; executed via TASK-079. |
| 1 Coordination integrity | DONE | Allocator + git lock + intake all live. |
| 2 Emergence cleanup | DONE | Stale report; stubs closed; TASK-052 records closed; Phase 2.4 decided via DEC-013 + SYN-0001. |
| 3 Observability | DONE | Event validator; metrics aliases (TASK-081); reconcile run; current-state.md refreshed (TASK-082) and shared-state validation passes (18 files). |
| 4 Portfolio hygiene | DONE | Onion bridge note; small projects untouched; lab remains test surface. |

## Recommended Tasks A-H

| Report task | Executed as | Status |
|---|---|---|
| A Canonical repo decision | DEC-012 (TASK-077) | DONE (operator-delegated) |
| B Atomic IDs | TASK-065 | APPROVED |
| C Git lock | TASK-065 | APPROVED |
| D Emergence stale report | TASK-065 | APPROVED |
| E Emergence index cleanup | TASK-075 | APPROVED |
| F Event validator | TASK-065 | APPROVED |
| G Availability reconcile | TASK-065 + TASK-082 run/semantics | DONE |
| H Approval calibration guide | TASK-065 doc | DONE |

## LangGraph flow verification (operator directive #15008)

`graph/runner.py` (venv python) routes correctly against post-remediation
state — and productively: it flagged TASK-063/064/065 sitting SUBMITTED with
no reviewer, which drove three independent peer reviews (all APPROVED,
records in artifacts/reviews/task06{3,4,5}-review-rose.md). After approvals
it routes `wait_or_reconcile` with an empty review queue. The runner needs
`MAP_System/.venv/bin/python` (system python lacks langgraph) — noted, not a
defect.

## Residual open items (all tracked, none blocking)

- Historical event-log warnings (33) — by design; normalize only if ever needed.
- `aider_wrapper.py` RECOMMENDED fix (TASK-050) and `local_runner.py` cosmetics
  (TASK-051) — pre-existing backlog, unchanged by the report.
- Stale archive `~/Projects/MultiAgentProject-stale-archive-20260702/` —
  deletable on operator confirmation.
- Experiments (EXP-*) still unused — per DEC-013 that is normal until a
  genuinely testable claim appears.
