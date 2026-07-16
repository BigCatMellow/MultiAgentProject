# Command Center UI Artifacts

Use this folder for historical evidence related to the Command Center UI
prototype and repairs that affected MAP state.

Current Command Center UI project work lives outside this repo at
`/home/home/Projects/CommandCenterUI` (confirmed by TASK-135's integration
plan and `shared/canonical-repo.md`; there is no `Projects/CommandCenterUI/`
inside this repo — `Projects/` here holds `Pathwell`, `ProjectUpdater`, and
`Backups` only). Treat this folder as provenance unless a current task
points here.

## Mission-Control TUI Prototype Path

TASK-150 points here for the next operator-control artifact:

```text
MAP_System/artifacts/command-center-ui/mission-control-textual-prototype.md
```

The intended prototype stack is Python Textual with a k9s-style terminal
interaction model. The first prototype is read-only: it should aggregate
durable MAP state (`map.db`, task files, `workflow/task_graph.json`,
`events/events.jsonl`, `agents/status.json`) plus hcom status/events, and it
must not become a second source of truth.

Write interventions are explicitly deferred until the read-only state is
accurate. Future keys for approve/reject, resume agent, kill runaway work,
bump budget, or override a false halt must call sanctioned MAP/hcom commands;
the TUI must never hand-edit canonical files or SQLite state.
