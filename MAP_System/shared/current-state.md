<!-- hpom: file: shared/current-state.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-02 -->
<!-- hpom: verified_against: TASK-065 MAP audit remediation batch -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Current State

Last reviewed during the MAP audit remediation batch.

## Live Capabilities

- Normal root Git is available for Aider and standard Git tooling.
- GitHub remote `origin` points to
  `https://github.com/BigCatMellow/MultiAgentProject.git`.
- SQLite-backed task claiming exists in `db/claims.py` and `map.db`.
- The LangGraph runner lives in `graph/runner.py`.
- The autonomous claim loop lives in `scripts/agent_loop.py`.
- File-backed task mirrors live in `tasks/` and `workflow/task_graph.json`.
- Agent availability lives in `agents/status.json`.
- Integration and multi-gate regression tests are wired into `scripts/run_tests.sh` (18 checks, all passing after TASK-065).
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
- `/home/home/Projects/MultiAgentProject` is not canonical and should not be a
  push/sync source until reconciled; use `/home/home/Downloads/MultiAgentProject`
  as the canonical local repo per `shared/canonical-repo.md`.
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
