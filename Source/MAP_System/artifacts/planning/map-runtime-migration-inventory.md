# MAP Runtime Migration Inventory (TASK-148)

Owner: claude-lab-zera
Date: 2026-07-13
Companion: `map-613-master-implementation-plan.md`, `map-runtime-migration-plan.md`

Purpose: name every piece of durable/live MAP state that a Wave 1+ runtime
change (single entry point, trace schema, cost governance, halt authority,
resilience controls, governance gates) could touch or drift, before any of
those waves start writing new fields, tables, or files. This inventory is the
input to the rollout plan; it does not itself authorize any change.

## 1. Canonical Repo And Git State

- Canonical local repo: `/home/home/Projects/MultiAgentProject` (DEC-014,
  `shared/canonical-repo.md`). Retired path:
  `/home/home/Downloads/MultiAgentProject` — must stay untouched/ignored.
- Git: normal root `.git`, branch `main`, remote
  `https://github.com/BigCatMellow/MultiAgentProject.git`
  (`notes/git-setup.md`).
- Preserved backups not to be deleted: `.git-empty-2026-06-28/`,
  `MAP_System/.git-unused-2026-06-28/`.
- Git-global operations require `scripts/git_operation_lock.py`; any new
  runtime migration script that touches repo-wide state (e.g. rewriting event
  schema across all history) must acquire this lock.

## 2. SQLite Canonical State (`MAP_System/map.db`)

- `tasks` table — canonical task status, claims, leases, attempts.
- `agents` table — registered agent identities (42+ rows as of this task;
  confirmed the registration path is manual/ad hoc — no script inserts new
  agents automatically, which is itself a migration risk, see Section 7).
- Task claim/lease logic: `db/claims.py` (`claim_task`, `heartbeat`,
  `submit_task`, `expire_leases`).
- Any new column (trace_id, parent_event_id, cost fields, gap_score,
  task_tier, halt state) is an ALTER TABLE against this live file with
  existing rows — must be additive/nullable, never a rewrite-in-place of
  existing rows without a backup.

## 3. File-Backed Task Mirrors

- `MAP_System/tasks/TASK-*.json` — one file per task, hand/script-edited.
- `MAP_System/workflow/task_graph.json` — 3,438 lines as of this inventory;
  single JSON document holding every task node and dependency edge.
- `scripts/validate_task_mirrors.py` — the gate that currently catches drift
  between SQLite, task JSON, and task graph. Any new required field (e.g.
  `trace_id`) must be added to all three surfaces in the same change or this
  gate will start failing existing tasks that predate the field.

## 4. Event Log

- `MAP_System/events/events.jsonl` — 821 lines as of this inventory,
  append-only.
- `events/warning_baseline.json` — accepted historical schema warnings;
  `scripts/validate_events.py --fail-on-new` only fails NEW warnings.
- Wave 2 (trace schema) and Wave 3 (cost fields) both add required/optional
  fields here. Precedent already exists (the warning-baseline mechanism) for
  adding fields without breaking old lines — reuse it rather than inventing a
  second compatibility mechanism.

## 5. Agent Status And Live Session State

- `MAP_System/agents/status.json` — durable, human/agent-edited record of
  agent availability (`available`, `standby`, `out_of_tokens`, etc.).
- Live hcom session state (`hcom list`, `hcom events`) — not durable, must be
  reconciled against `status.json` via `scripts/reconcile_agents.py`, which
  currently only reports drift and does not write to either side.
- `map.db.agents` (Section 2) is a THIRD copy of agent identity that
  `reconcile_agents.py` does not touch at all. This inventory step surfaced a
  live gap: a brand-new agent (this session, `claude-lab-zera`) was not
  registered in `map.db.agents`, causing an FK failure on task claim, and had
  to be inserted manually. No script currently keeps `status.json` and
  `map.db.agents` in sync. Flagged as a migration risk in the rollout plan
  (Section 4).
- `agents/README.md` documents identity-kind semantics (core vs. capability
  vs. helper).

## 6. Helper And Handoff State

- `MAP_System/inbox/helpers/*.md` — durable notes for active temporary
  helpers; currently 2 files (`helper-review-task-137.md`,
  `helper-antigravity-review-submissions.md`) plus README.
- `MAP_System/handoffs/HANDOFF-*.md` and `STATE_SNAPSHOT-*.yaml` — resume
  context for interrupted work; newest handoffs already reference this task's
  own predecessor work (TASK-090).
- `.locks/` — `agent_loop`, `emergence-ins.lock`, `emergence-promo.lock`,
  `limit-watcher.pid`. Any new resilience/circuit-breaker mechanism (Wave 7)
  that introduces its own lock file must land here and be named
  consistently, or `git-setup.md`/`AGENTS.md` need an update documenting it.

## 7. Registered Agent Identity Set (as observed 2026-07-13)

Distinct agent_ids present in `map.db.agents` but NOT all present in
`agents/status.json` (or vice versa) — a live example of the drift the
migration plan must close before Wave 1 adds new per-agent runtime state
(cost budgets, circuit-breaker status, task-tier eligibility):

- In `map.db` but absent from `status.json`: `bula`, `claude-bono`,
  `claude-lab-fema`, `claude-lab-fifi`, `claude-lab-kiri`, `claude-lab-miro`,
  `claude-lab-nuzo`, `claude-lab-rose`, `claude-lab-taro`, `claude-mako`,
  `claude-muse`, `codex-lab-kana`, `codex-lab-lepa`, `codex-lab-maki`,
  `codex-lab-memo`, `codex-lab-milo`, `codex-lab-nora`, `codex-lab-zanu`,
  `codex-lab-zune`, `codex-live`, `codex-tori`, `codex-vera`,
  `langgraph-runner`, `limit-watcher`, `map-task`, `reconcile`,
  `scratch-peso`.
- These are a mix of retired lab sessions, non-agent service identities used
  as `sender` in events (`map-task`, `reconcile`, `langgraph-runner`,
  `limit-watcher`), and stale entries. No current process prunes either
  table. New per-agent runtime fields (Wave 3 cost budgets, Wave 7 circuit
  breakers) must define whether they apply to every `map.db.agents` row or
  only to rows also present in `status.json` — otherwise retired identities
  silently accumulate budget/circuit-breaker state that nobody reads.

## 8. CommandCenterUI Assumptions

- `MAP_System/HUMAN_INTERFACE_SYSTEM.md` (DEC-019, TASK-110) is the content
  contract the CommandCenterUI prototype should surface. It specifies
  content, not implementation, and explicitly does not require a rebuild.
- The actual CommandCenterUI application lives outside this repo at
  `/home/home/Projects/CommandCenterUI` (confirmed via TASK-135's
  integration plan) — a separate codebase with its own deploy/restart
  lifecycle. Any Wave 1 single-entry-point or Wave 2 trace-reconstruction
  feature that expects a UI surface must treat CommandCenterUI as an
  external consumer with its own migration step, not part of this repo's
  atomic change set.
- `artifacts/command-center-ui/` in this repo holds the CommandCenterUI
  prototype/content-contract artifacts, not the live app.

## 9. Multi-Project / Pathwell State

- `Projects/Pathwell/` shares this repo, this `map.db`, this task graph, and
  this event log — it is not a separate MAP instance. `Projects/Pathwell/AGENTS.md`
  and `CLAUDE.md` point back to `MAP_System/AGENTS.md` and `MAP_System/CLAUDE.md`.
  Pathwell has its own `Story_Files/`, `insights/`, `synthesis/`, `ideas/`,
  `experiments/` folders, but those are content, not infrastructure.
  `Projects/ProjectUpdater/` is a separate standalone static app (browser
  `localStorage`-backed) integrated only through CommandCenterUI, not through
  MAP task/event state.
- Practical implication: any runtime migration (schema change, new lock,
  new validator) affects Pathwell's task/event stream identically, because
  there is one shared canonical store, not federated per-project stores.
  There is currently no per-project namespace on task IDs, event records, or
  agent budgets. Wave 3 cost governance and Wave 5 task tiering need to
  decide now whether budgets/tiers are global or per-project, because
  retrofitting a project dimension onto `tasks`/`events`/`agents` after those
  waves ship is a second migration.

## 10. Governance And Systems Documents (content contracts, not runtime state, but referenced by new gates)

- `AGENT_PERMISSION_LEVELS.md`, `DESTRUCTIVE_ACTION_POLICY.md`,
  `DECISION_CLASSES.md` — Wave 8's pre-dispatch policy checker reads these
  directly; they are hand-maintained prose today, not machine-checkable
  schemas. A migration step should confirm they are structured enough
  (stable field names, enumerable classes) for a script to parse before Wave
  8 is built against them, or the checker will need its own translation
  layer.
- `shared/decisions.md`, `shared/improvement-backlog.md`,
  `shared/current-state.md` — durable narrative state that must be updated
  in the same change set as any runtime schema change, per the existing HPOM
  gates (`validate_shared_state.py` requires 9 HPOM fields per shared file
  and rejects stale files).

## Summary Of Live Drift Found During This Inventory

1. `map.db.agents` and `agents/status.json` are two independently-maintained
   agent identity lists with no reconciliation script that writes to either
   — confirmed live during this task when registering `claude-lab-zera`.
2. `workflow/task_graph.json` and the per-task JSON files require synchronized
   manual edits on every status change; `validate_task_mirrors.py` catches
   drift after the fact but nothing prevents it beforehand.
3. CommandCenterUI is a separate, externally-hosted codebase; any runtime
   change that assumes a UI surface exists in this repo is wrong.
4. Pathwell and any future project share all MAP infrastructure with no
   per-project namespace — a decision, not yet made, that several Wave 3/5
   fields depend on.
