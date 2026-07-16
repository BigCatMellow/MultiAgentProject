<!-- hpom: file: shared/current-state.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: TASK-182/183 release pass -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# Current State

Last reviewed during TASK-193 (first brain compaction, 2026-07-14). Compacted
history for the TASK-147–192 era lives in
`archive/compactions/compaction-2026-07-14-tasks-147-192.md`.

## Live Capabilities

- Normal root Git is available for Aider and standard Git tooling.
- GitHub remote `origin` points to
  `https://github.com/BigCatMellow/MultiAgentProject.git`.
- SQLite-backed task claiming exists in `db/claims.py` and `map.db`.
- The LangGraph runner lives in `graph/runner.py`.
- `requirements.txt` constrains LangGraph dependencies to the stable 1.x line
  (`langgraph>=1.0,<2.0`, `langchain-core>=1.0,<2.0`) based on the TASK-145
  Research Summary.
- The autonomous claim loop lives in `scripts/agent_loop.py`.
- File-backed task mirrors live in `tasks/` and `workflow/task_graph.json`.
- Agent availability lives in `agents/status.json`.
- Integration and multi-gate regression tests are wired into `scripts/run_tests.sh` (37 checks after TASK-143 and the event-warning baseline cleanup).
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
- `scripts/validate_task_mirrors.py` compares canonical SQLite task state with
  `tasks/TASK-*.json` and `workflow/task_graph.json`. `map_task.py approve`,
  `release_task.py`, and `scripts/run_tests.sh` run this gate so stale file
  mirrors fail before approval/release instead of relying on agent memory.
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
- Emergence records are compact-by-default and wikilinked (TASK-180/181/183,
  2026-07-14): new templates use terse `- label:` bullets, the generated
  INDEX wikilinks resolvable references, and `map_emergence.py compact`
  (dry-run default, `--apply`, idempotent) converts historical prose records
  without touching closed statuses. All active records are converted. Local
  models were trialed for the rewrites and rejected as not yet reliable
  (TASK-181 report: `artifacts/planning/emergence-local-librarian-report.md`).
- External CommandCenterUI is current with the MAP runtime (TASK-182,
  2026-07-14): read-only `GET /api/map/health` + a sidebar "MAP runtime" card
  showing runner route, librarian wikilink validation, session-replay index
  health, and RnS watcher state (ok/warn/error per source, 20s cache,
  per-source error isolation). Record:
  `artifacts/command-center-ui/task-182-map-health-cards.md`.
- Event log shape reporting lives in `scripts/validate_events.py`; default mode
  reports legacy aliases and missing optional canonical fields, while
  `--fail-on-new` uses `events/warning_baseline.json` to fail only warnings
  added after the accepted historical baseline.
- Git operation coordination lock tooling lives in `scripts/git_operation_lock.py`.
- Agent status reconciliation reporting lives in `scripts/reconcile_agents.py`.
- Operator request intake recommendation helper lives in `scripts/intake_request.py`.
- Canonical local repo status is recorded in `shared/canonical-repo.md`.
- Approval calibration rules are recorded in `shared/approval-calibration.md`.
- The eleven governance systems (DEC-015..026, TASK-103–126) are all built and
  cross-linked; each system doc is its own canonical reference:

| System | DEC | Doc |
|---|---|---|
| Research | DEC-015 | `RESEARCH_SYSTEM.md` + `templates/research/` |
| Self-Repair | DEC-016 | `SELF_REPAIR_SYSTEM.md` + `repairs/` |
| Context | DEC-017 | `CONTEXT_SYSTEM.md` |
| Decision/Authority | DEC-018 | `DECISION_AUTHORITY_SYSTEM.md`, `DECISION_CLASSES.md` |
| Human Interface | DEC-019 | `HUMAN_INTERFACE_SYSTEM.md` |
| Risk | DEC-020 | `RISK_SYSTEM.md` |
| Security/Permissions | DEC-021 | `SECURITY_PERMISSIONS_SYSTEM.md`, `AGENT_PERMISSION_LEVELS.md`, `DESTRUCTIVE_ACTION_POLICY.md` |
| Change Control | DEC-022 | `CHANGE_CONTROL_SYSTEM.md` |
| Project Bootstrapping | DEC-023 | `PROJECT_BOOTSTRAPPING_SYSTEM.md`, `NEW_PROJECT_WIZARD.md` |
| Archive/Retention | DEC-024 | `ARCHIVE_RETENTION_SYSTEM.md` |
| Retrospective | DEC-025 | `RETROSPECTIVE_SYSTEM.md` + `retros/` |
| Emergence capture mandatory | DEC-026 | `emergence/README.md`; release gate enforces "Emergence capture considered" |

- Systems-use posture (TASK-140/143): don't force every system into every
  task. Emergence is actively used and enforced; Research is invoked when a
  task needs sourced, current, external, or disputed facts.

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
| Event log report | `scripts/validate_events.py` | ACTIVE — reports legacy schema/type aliases and fails new warnings with `--fail-on-new` |
| Emergence stale report | `scripts/map_emergence.py stale` | ACTIVE — reports stale, placeholder, and dangling emergence records |
| Git operation lock | `scripts/git_operation_lock.py` | ACTIVE — non-destructive lock for repo-global operations |
| Task mirror reconciliation | `scripts/validate_task_mirrors.py` | ACTIVE — blocks approval/release when SQLite, task JSON, or task graph mirrors drift |

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

- All shared files are CURRENT (validate_shared_state 21/21 as of 2026-07-14).
- Some historical artifacts still mention the old `langgraph/` directory. The live code path is `graph/`.
- Canonical repo is `/home/home/Projects/MultiAgentProject` per DEC-014 /
  `shared/canonical-repo.md` (supersedes DEC-012's Downloads path).
- `validate_events.py` reports 33 accepted legacy warnings; `--fail-on-new`
  with `events/warning_baseline.json` blocks new ones.
- `agents/limit-watcher-state.json` carries 10 open incidents (8 gave-up) for
  registered-but-idle early-July sessions. TASK-176's prune only removes
  incidents for agents absent from `agents/status.json`, so these persist and
  show as a warn in the CommandCenterUI MAP-runtime card. The ready next step
  is IDEA-0009's dry-run suppression experiment (treat superseded/disposable
  sessions as terminal), which TASK-146 triage marked ready-to-run.
- Open follow-up items are tracked in `shared/improvement-backlog.md`.
- Deferred command-center items are tracked in `notes/command-center-later.md`.
- Command Center Lab emergence integration is active through
  `scripts/map_emergence.py`; use capture when real insights, ideas,
  experiments, synthesis, or promotions appear, and skip ceremony when no
  candidate exists.

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
