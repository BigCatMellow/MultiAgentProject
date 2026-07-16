# MAP Mission-Control TUI Spec (TASK-150, Wave 2.5)

Status: draft-active
Owner: command-center
Built by: TASK-150

## Purpose

Mission control is the operator's live view of MAP: a terminal dashboard that
shows what the system is doing, what needs human attention, and where work is
stuck. It is a read-only aggregation first. It reads durable MAP and hcom
state and must not become a second source of truth.

Candidate stack: Python Textual with a k9s-style interaction model. Textual
fits the terminal workflow and gives enough layout, refresh, keyboard, and
mouse support for a polished multi-pane control surface.

Prototype path:

```text
MAP_System/artifacts/command-center-ui/mission-control-textual-prototype.md
```

That artifact should describe or capture a future read-only prototype. The
live CommandCenterUI app remains a separate repo at
`/home/home/Projects/CommandCenterUI`; this spec does not assume that repo is
changed by MAP_System tasks.

## Data Sources

| View | Source of truth |
|---|---|
| Task route and queues | `graph/runner.py`, `workflow/task_graph.json`, `map.db` |
| Task details and claims | `map.db`, `tasks/TASK-*.json` |
| Agent availability | `agents/status.json`, hcom list/events, future liveness surface |
| Events and traces | `events/events.jsonl`, TASK-149 trace fields |
| Reviews and approvals | `artifacts/reviews/`, `scripts/map_task.py approve/reject` |
| Risks and decisions | `shared/RISK_REGISTER.md`, `shared/decisions.md`, decision systems |
| Open repairs | `repairs/`, `SELF_REPAIR_SYSTEM.md` |
| Costs and budgets | Future Wave 3 cost fields |
| Halts and policy gates | Future Wave 4/Wave 8 validator outputs |

If a panel disagrees with these files or the database, the durable source
wins and the mismatch is a drift finding.

## Layout

The default layout is a dense, k9s-style dashboard:

```text
+--------------------------------------------------------------------------+
| Vitals: route | ready | in-flight | blocked | review | agents | budget   |
+----------------------+-----------------------------+---------------------+
| Roster               | Flight Board                | Attention Queue     |
| agent dots/state     | task rows / dependencies    | decisions needed    |
| lane / task / age    | owner / age / status        | halts / approvals   |
+----------------------+-----------------------------+---------------------+
| Event Stream: filtered canonical events and hcom attention items         |
+--------------------------------------------------------------------------+
```

Panels:

| Panel | Contents |
|---|---|
| Vitals bar | `next_route`, ready/submitted/in-progress/blocked counts, stale agents, active helpers, budget state once Wave 3 lands, validator state once Wave 4 lands. |
| Roster | Every core/helper/service identity, lane, active task, state, heartbeat age, and status reason. Heartbeat dots: green fresh, yellow idle/blocked/suspect, red broken, grey standby. |
| Flight board | Active and ready tasks, dependencies, owner, attempt, lease age, output paths summary, review state. Highlight tasks blocked longer than the configured threshold. |
| Attention queue | Only human-actionable items: approval gates, destructive-action requests, validator halts, budget breaches, stale/broken agents, unresolved conflicts, blocking repair/risk records. |
| Event stream | Filterable recent events by task, trace, sender, type, and hcom thread. Routine chatter stays out unless selected. |
| Status footer | Last refresh, source health, keyboard hints, and read-only/intervention mode indicator. |

## Drill-Down Views

Task drill-down:

- trace tree from TASK-149 fields when present;
- dependency chain and blockers;
- output paths and changed-file list;
- cost/latency once available;
- review findings and acceptance criteria;
- halt reason or policy gate when present.

Agent drill-down:

- current lane and task;
- recent hcom status events;
- heartbeat history;
- stale/reaper incidents;
- last handoff or state snapshot;
- claims and submissions in the current session.

Attention-item drill-down:

- why the item is actionable;
- source file/event IDs;
- available sanctioned commands;
- whether operator approval is required.

## Keybindings

Read-only keybindings should ship first:

| Key | Action |
|---|---|
| `q` | Quit |
| `r` | Refresh all sources |
| `/` | Filter current panel |
| `tab` / `shift-tab` | Move focus |
| `enter` | Open drill-down |
| `esc` | Close drill-down or clear filter |
| `t` | Task view |
| `a` | Agent roster |
| `e` | Event stream |
| `!` | Attention queue |
| `?` | Help |

Intervention keybindings are designed now but disabled until the read-only
view is correct:

| Key | Future intervention | Required backend |
|---|---|---|
| `A` | Approve selected submitted task or approval gate | `map_task.py approve` with review record or approval record |
| `R` | Request changes / reject selected submitted task | `map_task.py reject` |
| `K` | Kill or suspend runaway agent/task | liveness reaper and operator approval gate |
| `N` | Resume/nudge selected agent | existing visible hcom resume/nudge path |
| `B` | Bump budget | Wave 3 budget API |
| `O` | Override false halt | Wave 4/Wave 8 halt authority record |
| `D` | Dead-letter/replay task | Wave 7 dead-letter API |

All write interventions must call sanctioned MAP commands. The TUI must never
write `map.db`, task JSON, task graph, or event JSONL directly.

## Refresh And Failure Modes

- Default refresh: explicit `r` plus a short polling interval for hcom and
  runner state.
- On slow source: keep stale data visible with an age marker; do not blank
  the panel.
- On invalid source: show the validator error in the attention queue.
- On source disagreement: show a drift warning and link to the durable source.
- On hcom unavailable: keep MAP file/database panels available and mark hcom
  status degraded.

## Non-Goals For First Prototype

- No production writes.
- No budget mutation.
- No kill switch.
- No replacement for hcom chat.
- No separate task database.
- No live CommandCenterUI repo change.

The first prototype is successful when it accurately shows the same route,
queue, task, agent, and event state an operator would otherwise reconstruct
from `graph/runner.py`, `agents/status.json`, hcom, and durable MAP files.
