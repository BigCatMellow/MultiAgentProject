# Command-Center Runtime Exercise

Task: TASK-175
Owner: codex-lab-mozu
Date: 2026-07-14
Status: draft for review

## Purpose

Exercise the built MAP command-center stack with real commands after the
operator's directive to stop merely designing systems and start using them.
This is a runtime check of Command Center, LangGraph routing, RnS/liveness,
HPOM/pre-dispatch, mission-control, session replay, and external
CommandCenterUI currency.

No external CommandCenterUI files were edited.

## Commands Exercised

| Surface | Command | Result |
|---|---|---|
| LangGraph runner | `MAP_System/.venv/bin/python MAP_System/graph/runner.py` | PASS. Route computed successfully; current route `wait_or_reconcile`, in-progress `TASK-175`, no halt. |
| Command-center intake | `python3 MAP_System/scripts/command_center_intake.py --no-event --json "Exercise command center runtime surfaces and report active gaps"` | PASS. Produced dispatch packet, classified as `worker_fit=claude_or_codex`, `needs_task=yes`, `risk=medium`, `task_type=audit`; no event written due `--no-event`. |
| Mission-control JSON | `python3 MAP_System/scripts/mission_control_tui.py --json` | PASS with stale liveness findings. Dashboard renders runner, vitals, flight board, event stream, drift, and dead-letter state; roster evidence is stale when `shared/liveness-state.md` is not refreshed with hcom data. |
| RnS dry-run | `python3 MAP_System/scripts/limit_watcher.py --once --dry-run` | PASS but noisy/stale. It would probe old agents `claude-lab-fimo`, `claude-lab-rose`, and `codex-lab-duno`, and emits old TASK-083 events for presumed-down sessions. |
| HPOM/pre-dispatch | `python3 MAP_System/scripts/pre_dispatch_policy.py --task-id TASK-175 --candidate-worker codex-lab-mozu --worker-tier 4 --assignment-mode core --json` | PASS. Decision `allow`, reason `ALLOW_WITHIN_TIER`. |
| Session replay | `python3 MAP_System/scripts/session_replay.py status` | PASS. Derived index exists, `safe_for_mission_control=true`, `drift_findings=[]`, `row_counts.map_events_jsonl=927`. |
| Liveness with live hcom | `hcom list --json --name mozu`, transformed to agent-keyed JSON, then `python3 MAP_System/scripts/liveness_reaper.py --hcom-json /tmp/hcom-status-by-agent.json --json` | PARTIAL. Correctly marks `codex-lab-mozu` as `working` on TASK-175 and `claude-lab-zera` as `alive`, but `liveness_reaper.py` cannot consume raw `hcom list --json` directly because hcom emits a list while the script expects an agent-keyed object. |
| External CommandCenterUI read-only scan | `find`, `rg`, `git -C`, `node --check`, `bash -n` under `/home/home/Projects/CommandCenterUI` | PARTIAL. Existing app is real and has hcom/feed/terminal/approval features, but no references to TASK-171/172/173, `session_replay`, or `librarian`; it is not current with today's MAP runtime additions. |

## What Is Actively Working

- LangGraph runner is the active route source. It sees live MAP tasks from
  SQLite and routed the current state without errors.
- Command-center intake wrapper is usable as a mechanical intake dry-run. It
  classifies broad operator text and emits a decomposer contract without
  needing an agent to invent the packet manually.
- HPOM/pre-dispatch gates are callable against real task IDs and can be used
  as an exercise check before claiming work.
- Session replay is now live infrastructure, not a design. The derived index
  built from MAP sources is healthy and queryable.
- Mission-control JSON aggregates runner, flight board, attention, drift, and
  recent events. It is useful but only as accurate as its liveness input.
- External CommandCenterUI is a real app with hcom read-only DB access,
  guarded send paths, terminal viewing/injection, and approval-related code.
  JavaScript and shell syntax checks pass.
- Zera exercised the visible-helper path by launching a visible
  `librarian-batch2` helper with a durable helper note, matching the operator's
  request to use helper agents when useful.

## Gaps Found

### 1. Mission-Control Liveness Uses Stale Evidence By Default

`mission_control_tui.py --json` showed active agents as suspect/broken because
it reads `shared/liveness-state.md`, which was not refreshed with live hcom
data. A direct liveness probe with transformed `hcom list --json` data
correctly identified:

- `codex-lab-mozu`: `working`, active task `TASK-175`, evidence
  `hcom:active;task:IN_PROGRESS`;
- `claude-lab-zera`: `alive`, evidence `hcom:active`.

Concrete follow-up:

- Add a liveness refresh adapter that accepts raw `hcom list --json` output
  directly and updates the mission-control liveness snapshot, or have
  mission-control call a read-only hcom-status adapter before rendering.

### 2. `liveness_reaper.py --hcom-json` Input Shape Does Not Match `hcom list --json`

Raw `hcom list --json` returns a list of records. `liveness_reaper.py` expects
an agent-keyed object and fails with:

```text
AttributeError: 'list' object has no attribute 'get'
```

The workaround was to transform the list into:

```json
{
  "codex-lab-mozu": {
    "status": "active",
    "status_age_seconds": 0,
    "context": "tool:list",
    "detail": ""
  }
}
```

Concrete follow-up:

- Teach `liveness_reaper.py` to accept both shapes. This is small and would
  remove the current glue step between hcom and mission-control.

### 3. RnS Dry-Run Is Still Carrying Old Session Noise

`limit_watcher.py --once --dry-run` works and uses visible `wezterm-tab`
resumes, but it wants to probe old sessions:

- `claude-lab-fimo`
- `claude-lab-rose`
- `codex-lab-duno`

It also emits old TASK-083 presumed-down events for old map613 helper sessions.

Concrete follow-up:

- Add an RnS cleanup/calibration task to retire or archive superseded watcher
  targets so the watcher focuses on current lab agents and does not normalize
  stale historical noise.

### 4. External CommandCenterUI Is Not Current With TASK-171 Through TASK-174

Read-only scan of `/home/home/Projects/CommandCenterUI` found:

- Last commits are TASK-092 through TASK-094 era.
- Current working tree is dirty:
  - `README.md`
  - `app/server.py`
  - `src/chat.css`
  - `src/chat.html`
  - `src/chat.js`
  - `project-updater-status.json`
- No references were found to `session_replay`, `librarian`, or the new
  TASK-171 through TASK-174 runtime additions.
- Syntax checks:
  - `node --check src/app-live.js src/chat.js src/studio.js`: pass.
  - `bash -n run-command-center-app.sh launch-command-center-ui.sh`: pass.
  - Python compile requires `PYTHONPYCACHEPREFIX=/tmp/...` in this sandbox
    because this session cannot write `__pycache__` under the external repo;
    with that prefix, `app/server.py` and `app/window.py` compile.

Concrete follow-up:

- Create a separate external-UI task if the operator wants CommandCenterUI
  updated now. It should add read-only endpoints/cards for:
  - session replay health and task/trace query links;
  - librarian validation status and backlink/coverage summary;
  - current runner route and stale-liveness warning;
  - RnS stale-target count.

This requires explicit external output paths under
`/home/home/Projects/CommandCenterUI` because those files are outside this MAP
task's writable ownership.

### 5. Command-Center Intake Exists But Direct Chat Still Bypasses It

The intake wrapper works, but the live session still receives direct broad
operator instructions through hcom. That is allowed by current policy for live
control, but it means the single-entry-point goal is procedural, not enforced.

Concrete follow-up:

- Add an operator-facing convention or command-center wrapper that turns broad
  chat directives into a visible intake packet first, while still allowing
  urgent hcom control messages.

## Recommended Next Implementation Tasks

1. **Liveness adapter task**: make `liveness_reaper.py` accept raw
   `hcom list --json` list output and add a mission-control refresh path.
2. **RnS cleanup task**: retire stale watcher targets and record why old
   helper sessions are no longer probe candidates.
3. **External CommandCenterUI currency task**: update the standalone app with
   read-only cards for session replay, librarian validation, and current MAP
   route/liveness state.
4. **Intake usage task**: make command-center intake the default wrapper for
   broad operator directives, with a clear exception for urgent live control.

## Bottom Line

The MAP command-center stack is no longer just design: runner, intake, HPOM,
mission-control, RnS, session replay, librarian validation, and helper launch
paths all execute. The main weakness is integration freshness. The pieces work,
but mission-control and the external UI do not yet consume the newest state
directly enough to be the operator's reliable single pane.
