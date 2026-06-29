# STATE_SNAPSHOT — Session End 2026-06-23

agent_id: claude-bono
session_id: 6296e54b-ecbc-48fd-b58b-bf9c8673e6d1
status: paused — operator pause, Codex out of tokens

---

## Project Status

**All 33 tasks DONE or APPROVED. Bootstrap phase complete.**

- DONE (20): TASK-001 through TASK-020
- APPROVED (13): TASK-021 through TASK-033

No active claims. No pending approval gates. No open unresolved questions that block work.

---

## What Was Built This Session

- **TASK-028 fixed**: `Command(resume=None)` → `Command(resume=True)` in agent_loop.py. Root cause: LangGraph 1.2.5 assigns `resume_is_map` only inside `if resume is not None:` but references it outside; `None` caused `UnboundLocalError`.
- **TASK-030 implemented + fixed**: Multi-gate approval handling in runner.py. Each pending gate gets one `interrupt()` call; payload shows all remaining gates. `--approve`/`--reject` now take `GATE_ID`; `--thread-id` is always explicit. Bug found by Codex review: pending gates reloaded from SQLite each re-execution, shrinking interrupt count and drifting positions. Fixed by `load_all_approval_gates` (stable rowid order) — resolved gates return checkpoint values immediately.
- **TASK-031/032/033 reviewed and approved**: CI test runner, retry cooldown, map-task CLI — all LGTM.
- **Guidelines audit**: 7/8 already followed. Gap: `ai-improvement-scout-protocol.md` requires `## Improvements Checked` block on all task completions. Applied going forward.

---

## Active Constraints

- Codex + Claude only (DEC-008). Antigravity/Gemini are standby.
- All spawned helpers must use `--terminal wezterm-tab` (never `--headless`).
- `Command(resume=True)` not `Command(resume=None)` when resuming agent_loop interrupts.
- `ai-improvement-scout-protocol.md`: every task completion needs `## Improvements Checked` section.
- MATOCP v3.2 token grammar applies to all agent-to-agent messages.

---

## Next Steps (when resuming)

1. **Define first real workflow** — the platform is operational; the natural next step is picking a real use-case (software project, research, writing) to run on it. Discussed in `shared/unresolved-questions.md`.
2. **Optional cleanup**: Add the approve-then-reject regression fixture to `run_tests.sh` (recommended by Codex in TASK-030 review).
3. **Optional**: Resolve open questions in `shared/unresolved-questions.md` — branch strategy, LangGraph model/provider selection, first workflow target.

---

## Key File Locations

- Task board: `MAP_System/tasks/TASK-NNN.json` + `MAP_System/map.db`
- Events: `MAP_System/events/events.jsonl`
- Guidelines: `MAP_System/Guidelines/` (8 docs)
- Live status: `MAP_System/.venv/bin/python MAP_System/scripts/map_status.py`
- CI: `MAP_System/scripts/run_tests.sh`
- Decisions: `MAP_System/shared/decisions.md`

---

lexicon:
  resume_is_map: "LangGraph internal bool; assigned only when resume is not None — pass True not None"
  load_all_approval_gates: "runner.py fn; loads all gates in rowid order for stable interrupt positions"
