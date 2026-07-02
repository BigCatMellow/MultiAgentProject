<!-- hpom: file: shared/current-state.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-02 -->
<!-- hpom: verified_against: TASK-082 full-report coverage pass (post TASK-079/080 reconciliation and watcher) -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Current State

Last reviewed during the TASK-082 full-report coverage pass.

## Live Capabilities

- Normal root Git is available for Aider and standard Git tooling.
- GitHub remote `origin` points to
  `https://github.com/BigCatMellow/MultiAgentProject.git`.
- SQLite-backed task claiming exists in `db/claims.py` and `map.db`.
- The LangGraph runner lives in `graph/runner.py`.
- The autonomous claim loop lives in `scripts/agent_loop.py`.
- File-backed task mirrors live in `tasks/` and `workflow/task_graph.json`.
- Agent availability lives in `agents/status.json`.
- Integration and multi-gate regression tests are wired into `scripts/run_tests.sh` (22 checks, all passing after TASK-080/081).
- The limit watcher (`scripts/limit_watcher.py`, TASK-080, APPROVED) runs in the
  background and auto-resumes agents after usage-limit resets: the default poll
  interval is 90 minutes (`5400s`), chosen against the 5-hour agent refresh
  window. It polls `agents/status.json` for `out_of_tokens` + ISO-8601
  `resume_after`, resumes via visible `hcom r <name> --terminal wezterm-tab`
  (one nudge per window), and reports silent stops. Start/stop:
  `scripts/start-limit-watcher.sh` /
  `kill $(cat .locks/limit-watcher.pid)`. Protocol: `notes/limit-exhaustion-protocol.md`.
- `map_task.py rework` returns a CHANGES_REQUESTED task to a claimable state
  (TASK-081; closes the rework dead-end found during TASK-080's rejection).
- A release-path smoke checklist for user-facing packages lives in
  `notes/release-path-checklist.md` (PROMO-0005). A security second-pass rule
  for network-facing/write-capable outputs is in `AGENTS.md` Review Standard
  (PROMO-0004).
- Task graph validation currently passes.
- `scripts/map_task.py create --task-id auto` allocates the next task ID under
  a SQLite write lock so concurrent agents do not manually collide on task IDs.
- Local Ollama helper runner lives in `scripts/local_runner.py` (TASK-048, APPROVED).
- Supervised Aider setup wrapper lives in `scripts/aider_wrapper.py` (TASK-049, APPROVED).
- Emergence capture tooling lives in `scripts/map_emergence.py`. It can create
  insight, synthesis, idea, experiment, and promotion records from templates,
  rebuild `emergence/INDEX.md`, print the registry, validate artifact files,
  and report stale/placeholder lifecycle issues with `map_emergence.py stale`.
- Event log shape reporting lives in `scripts/validate_events.py`; default mode
  warns on legacy aliases and missing optional canonical fields without failing
  historical logs.
- Git operation coordination lock tooling lives in `scripts/git_operation_lock.py`.
- Agent status reconciliation reporting lives in `scripts/reconcile_agents.py`.
- Operator request intake recommendation helper lives in `scripts/intake_request.py`.
- Canonical local repo status is recorded in `shared/canonical-repo.md`.
- Approval calibration rules are recorded in `shared/approval-calibration.md`.

### HPOM Gates (all active as of 2026-06-29)

| Gate | Script | Status |
|---|---|---|
| READY promotion | `scripts/promote_task.py` | ACTIVE — blocks CONFLICT tasks, requires 8 HPOM fields |
| No-self-review (claim) | `db/claims.py` `claim_block_reason()` | ACTIVE — claim fails if agent == task owner on review tasks |
| Review gate | `scripts/validate_review.py` + `map_task.py approve --review-record` | ACTIVE — APPROVED requires valid review record |
| Release gate | `scripts/release_task.py` + `map_task.py release --checklist` | ACTIVE — RELEASED requires completed checklist + record |
| Conflict freeze | `scripts/flag_conflict.py` | ACTIVE — CONFLICT status blocks promotion |
| Shared-state metadata | `scripts/validate_shared_state.py` | ACTIVE — 9 HPOM fields required per shared file |
| Decision log | `scripts/validate_decisions.py` | ACTIVE — required fields checked, index auto-generated |
| Metrics dashboard | `scripts/map_metrics.py` | ACTIVE — read-only health report (text + JSON) |
| Task ID allocation | `scripts/map_task.py create --task-id auto` | ACTIVE — reserves next TASK-NNN inside SQLite write transaction |
| Event log report | `scripts/validate_events.py` | ACTIVE — reports legacy schema/type aliases |
| Emergence stale report | `scripts/map_emergence.py stale` | ACTIVE — reports stale, placeholder, and dangling emergence records |
| Git operation lock | `scripts/git_operation_lock.py` | ACTIVE — non-destructive lock for repo-global operations |

## Active Agents

- Codex and Claude Code are the active core agents.
- Gemini and Antigravity are standby/manual unless the operator explicitly activates them.
- Temporary helpers are allowed when task-scoped and recorded in `inbox/helpers/`.
- Local Ollama models and Aider are helper capabilities, not registered core agents; see `notes/local-model-helper-guide.md`.
- Local assistants should take scoped support load off paid/core agents through
  summaries, checks, drafts, recommendations, and diff suggestions.
- HPOM is now defined as the Human-Paced Orchestration Model: a routing and
  assignment discipline for deciding when to use humans, core agents, helpers,
  local models, or Aider. See `shared/hpom.md` and
  `shared/agent-capability-matrix.md`.

## Known Health Issues

- All shared files are CURRENT (0 stale as of 2026-06-29).
- Some historical artifacts still mention the old `langgraph/` directory. The live code path is `graph/`.
- `aider_wrapper.py` has one open RECOMMENDED fix: remove `--no-auto-commits` from `FORBIDDEN_AIDER_FLAGS` (tracked as TASK-050).
- `local_runner.py` has two OPTIONAL cosmetic items (tracked as TASK-051).
- Repo reconciliation is COMPLETE (TASK-079, 2026-07-02): canonical repo A
  pushed to origin at `5cb8a61`; `/home/home/Projects/MultiAgentProject` is now
  a fresh clone of that commit with private `Projects/Pathwell` + `Projects/Backups`
  restored from A; the old drifted copy is preserved at
  `~/Projects/MultiAgentProject-stale-archive-20260702/` (do not use). A remains
  the canonical working repo per DEC-012 / `shared/canonical-repo.md`.
- `agents/status.json` was reconciled to hcom reality on 2026-07-02 (TASK-082);
  identity-kind semantics are documented in `agents/README.md`.
- `validate_events.py` currently reports legacy event warnings in the historical
  event log; this is expected until an event-normalization task runs.
- Open follow-up items are tracked in `shared/improvement-backlog.md`.
- Deferred command-center items are tracked in `notes/command-center-later.md`.
- Command Center Lab emergence integration is being coordinated separately by
  Claude; core CLI contract is `insight|idea|experiment|synthesis TEXT`,
  `promote IDEA-id`, `list`, and `validate`.

## Safety Notes

- Normal root Git is available. `scripts/map-git` remains as a compatibility
  wrapper.
- Before using Aider for more than narrow helper edits, review and commit the
  current MAP cleanup/restructure so rollback points are clear.
- Treat `artifacts/` as historical unless a current task points to a specific artifact.
- Treat `archive/` as historical compacted memory unless a current task points to a specific archived file.
- Do not silently fill missing task acceptance criteria or output paths without understanding task intent.
- Handler commands passed to `scripts/agent_loop.py` are trusted operator configuration and should not be built from untrusted input.
- Run brain compaction periodically so active memory stays lean; see `notes/brain-compaction-guide.md`.
- Push back on changes that hide ownership, erase history, over-automate ambiguous work, or make active memory noisier.
