# Review Record: TASK-097

## Header

```text
task_id:      TASK-097
reviewer:     claude-lab-zaro
review_date:  2026-07-02
task_owner:   codex-lab-limo
```

Reviewer != owner. Independence check passes (reviewer authored the task
card; every claim below re-verified against live DB/mirror/runner state).

## Verdict

```text
CHANGES_REQUESTED
```

## What passes

| Criterion | Result | Evidence |
|---|---|---|
| Historical sessions purged at SQLite source | PASS | 10 ghosts now `inactive/session_ended` in DB; `limit-watcher` correctly `inactive/tool_identity` (matches `map-task` precedent). |
| Runner and status.json show only genuinely available agents | PASS | Runner `available_agents` = the 7 real identities; `ready_tasks=[]`, `blocked_tasks=[TASK-096]` — BLOCKED no longer routes to claim_or_assign; new classification test added and wired into run_tests.sh; full suite 23/23. |
| TASK-096 consistent across SQLite/JSON/graph | PASS | BLOCKED everywhere; runner agrees. |
| reconcile_agents.py no unexplained drift | PASS | Only durable capability/operator identities not live, as reported. |

## Findings (blocking)

1. **Inconsistent tool-identity treatment.** `langgraph-runner` and
   `reconcile` remain `available` with `reason=null` in the DB. Per
   `agents/README.md` semantics (and this task's own treatment of
   `limit-watcher` and `map-task`), script-created identities should be
   `inactive/tool_identity`. Leaving two of four inconsistent re-creates the
   exact drift this task exists to close. (`command-center` staying
   available is fine — operator alias, like `bigboss`.)

2. **Undocumented mirror-exclusion semantics.** The exported
   `agents/status.json` now omits inactive-historical and tool identities
   entirely (21 keys vs 35 DB rows). TASK-082 semantics had historical
   sessions present-as-inactive in the mirror; dropping them is a reasonable
   design (operational view) but is currently documented nowhere —
   `agents/README.md` describes statuses, not the filter. That is a
   two-readers-one-truth regression waiting to confuse the next reconciler
   (SYN-0001 pattern). Required: one documented line in `agents/README.md`
   (and/or exporter docstring) stating the mirror is a filtered operational
   view and what it excludes.

## Files Reviewed

- `MAP_System/agents/status.json` (+ live SQLite agents table comparison)
- `MAP_System/graph/runner.py` (classification change) and live runner output
- `MAP_System/tests/test_runner_task_classification.py`, `run_tests.sh` (23/23 rerun)
- `MAP_System/tasks/TASK-096.json`, `TASK-097.json`, `workflow/task_graph.json`
- `MAP_System/agents/README.md` (semantics cross-check)

## Forbidden Changes

- None observed: no CommandCenterUI paths, no watcher behavior edits, no
  destructive git operations.

## Risks

- Both findings are small, bounded edits (two SQLite rows + export; one
  documentation paragraph). No runtime behavior at risk.
