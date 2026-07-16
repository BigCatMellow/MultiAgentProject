# Work Packet: Cost/Yield Rollup

Intended implementer: claude-lab-zero (TASK-186 implementation helper — proven
on bounded packets)
Dispatcher: claude-lab-mira (lead)
Status: awaiting task record (auto ID pending; confirmed over hcom before start)
Source: `artifacts/audits/source-mining-audit-2026-07-14.md` ranked item #3
(codeburn pattern, TASK-171 Priority 2 — the only TASK-171 priority with zero follow-on)

## Goal

Answer, from existing MAP data: "what did this task cost and did it produce
released work?" — a per-task cost × outcome rollup the operator can read.

## Design (follow; flag disagreement before deviating)

1. New `rollup` mode in `scripts/cost_governance.py` (or a sibling
   `scripts/cost_yield.py` if cleaner — your call, justify in the report):
   - join per-task signals: event counts/types per task_id from
     `events/events.jsonl`, lifecycle spans from `map.db` (created→claimed→
     submitted→approved→released timestamps), attempts, rework rounds.
   - classify outcome per task: RELEASED / APPROVED-not-released / RETIRED /
     abandoned (terminal-but-unreleased) — reuse existing status taxonomy.
   - emit productive-vs-abandoned spend split and a cost-by-released-output
     view. "Cost" = the proxy signals we actually have (event volume, wall-
     clock span, attempts, rework count) — label them proxies; do NOT invent
     dollar numbers.
   - reference vocabulary: `repo/codeburn-main/src/yield.ts` categories.
2. Text + `--json` output, matching `map_metrics.py` conventions.
3. Focused tests (fixture events/db) wired into `run_tests.sh`.
4. Run it for real; include the real output in your report.

## Rules

- Read-only against canonical state (no event writes from the rollup).
- Output paths will be registered on the task record before you start.
- Report to claude-lab-mira via hcom with files, test counts, real rollup output.
