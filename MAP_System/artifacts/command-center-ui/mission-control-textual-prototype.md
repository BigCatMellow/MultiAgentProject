# Mission-Control TUI Prototype (TASK-160)

Status: complete (first read-only prototype)
Owner: command-center
Built by: TASK-160
Source: `mission-control-tui-spec.md` (TASK-150)

## Stack Decision: curses, not Textual

The spec named Python Textual/k9s-style as the candidate stack. `textual`
is not installed in this repo's venv or system Python, and per this
session's working agreement with the operator (ask before any external
download/install, proceed autonomously otherwise), an install request was
sent via hcom. Rather than block the first prototype on that approval,
this task ships using Python's built-in `curses` module instead — zero new
dependencies, same read-only contract, same data layer. If the operator
approves `textual` later, only the rendering layer
(`_mission_control_app.py`) needs to be swapped; `mission_control_tui.py`'s
data-aggregation functions are stack-agnostic and unchanged either way.

## What Exists

`MAP_System/scripts/mission_control_tui.py` — the data-aggregation layer,
fully tested independent of any rendering library:

- `get_runner_snapshot()` — the single source of truth for route/queue
  state, read via `graph/runner.py --pretty`, never recomputed here.
- `get_vitals()` — route, ready/submitted/in-progress/blocked counts, halt
  state, available-agent count.
- `get_roster()` / `get_liveness_snapshot()` — parses the markdown table
  `liveness_reaper.py` (TASK-158) already produces at
  `shared/liveness-state.md`, rather than recomputing agent liveness state
  independently.
- `get_flight_board()` — ready/in-progress/submitted/blocked/dispatch-blocked
  task lists.
- `get_attention_queue()` — filters to human-decision-only items: tasks
  awaiting review, an active halt, and broken/suspect agents. Routine
  "working"/"idle" states are deliberately excluded.
- `get_event_stream()` — tails `events/events.jsonl`.
- `check_source_drift()` — reuses `validate_task_mirrors.py` (never
  reimplements the mirror comparison) to satisfy the spec's failure-mode
  rule: on source disagreement, show a drift warning, not a silent/blank
  panel.
- `build_dashboard_snapshot()` — one call producing everything a render
  layer needs.

`MAP_System/scripts/_mission_control_app.py` — the curses rendering layer.
Pure render functions (`render_vitals_line`, `render_roster_lines`,
`render_flight_board_lines`, `render_attention_lines`, `render_event_lines`)
are independently testable without a TTY; `draw()`/`_main_loop()`/`run_app()`
wire them into an interactive, auto-refreshing (every 5s, or on `r`)
terminal view.

Run:

```bash
python3 MAP_System/scripts/mission_control_tui.py --json   # snapshot only, no TTY needed
python3 MAP_System/scripts/mission_control_tui.py          # interactive curses view
```

## Read-Only Guarantee (Acceptance Criterion 2)

Two structural tests in `tests/test_mission_control_tui.py` — one for the
data layer, one for the rendering layer — assert no SQL write statements,
no file writes in append/write mode, and no subprocess calls to
write-capable scripts (`map_task.py`, `export_to_files.py`,
`liveness_reaper.py --act`, `release_task.py`) appear anywhere in either
module's source.

## Drift Handling (Acceptance Criterion 3)

`check_source_drift()` runs `validate_task_mirrors.py` and, on
disagreement, `draw()` renders a `!! MIRROR DRIFT: <detail>` line directly
under the vitals bar rather than a blank or silently-stale panel.

## Keybindings (Acceptance Criterion 4)

`READ_ONLY_KEYBINDINGS` (q/r/tab/shift+tab/enter/esc/t/a/e/!/?) are wired
in `_main_loop()`: `q` quits, `r` forces an immediate refresh, `?` opens a
help overlay listing every binding (both read-only and disabled). All
other read-only navigation keys are accepted but currently no-op (single
dense view in this first prototype, per the spec's minimal first version).
`DISABLED_INTERVENTION_KEYBINDINGS` (A/R/K/N/B/O/D) are documented in the
help overlay as explicitly disabled — per the spec's "Non-Goals For First
Prototype" list (no production writes, no budget mutation, no kill switch,
no dead-letter replay from the UI) — with no code path that calls a write
function for any of them.

## If `textual` Is Approved Later

1. Create a Textual `App` subclass whose panels render exactly the dicts
   `build_dashboard_snapshot()` already returns — no new data logic there.
2. Port `READ_ONLY_KEYBINDINGS`/`DISABLED_INTERVENTION_KEYBINDINGS` to
   Textual's `BINDINGS` list.
3. The existing fixture-based render tests
   (`test_render_vitals_line_formats_key_fields` and siblings) test the
   pure-function layer, which a Textual port would reuse unchanged.

## Related Files

- `MAP_System/scripts/mission_control_tui.py`
- `MAP_System/scripts/_mission_control_app.py`
- `MAP_System/tests/test_mission_control_tui.py`
- `MAP_System/artifacts/planning/mission-control-tui-spec.md` [[mission-control-tui-spec]]
- `MAP_System/scripts/liveness_reaper.py` (TASK-158, liveness data source)
- `MAP_System/artifacts/command-center-ui/README.md` [[artifacts/command-center-ui/README]]
