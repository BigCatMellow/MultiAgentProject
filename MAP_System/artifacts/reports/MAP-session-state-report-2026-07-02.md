# MAP Session State Report - 2026-07-02

Generated: 2026-07-02 08:00 EDT
Prepared by: codex-lab-limo
Primary repo: `/home/home/Downloads/MultiAgentProject`

## Executive State

- Canonical repo is `/home/home/Downloads/MultiAgentProject` per DEC-012.
- Last clean pushed commit before this report: `6e7d23f` -
  `RnS v2.1: declared-idle protocol and 2h check-in nudges (TASK-084)`.
- Core live agents: `codex-lab-limo` and `claude-lab-rose`.
- Gemini and Antigravity remain standby/manual unless the operator activates
  them.
- RnS now covers both usage-limit recovery and declared-idle check-ins.
- Lab-open autostart is approved in TASK-085: opening the lab starts RnS and
  boots both lab agents with one proactive startup-orientation message.

## Session Changes

### Repo And Git State

- DEC-012 established `/home/home/Downloads/MultiAgentProject` as the canonical
  repo.
- Repo B at `/home/home/Projects/MultiAgentProject` was reconciled by TASK-079:
  preserved private Pathwell/Backups content, recloned from origin, and left old
  drift in `~/Projects/MultiAgentProject-stale-archive-20260702/`.
- Root Git is now the normal path; `MAP_System/scripts/map-git` remains as a
  compatibility wrapper.
- A non-destructive git operation lock exists for coordinated repo-global work.
- Current untracked `Projects/` content in the canonical repo is expected
  private/unrelated material and should not be staged casually.

### Task Workflow

- Task ID allocation was hardened with SQLite-backed auto allocation so
  concurrent agents do not collide on manual task numbers.
- `map_task.py rework` now returns CHANGES_REQUESTED work to a claimable state,
  closing the rework dead-end found during TASK-080 review.
- Review and release gates remain active:
  - no self-review for substantive deliverables;
  - review records required for approval;
  - release checklist required for release;
  - network-facing/write-capable outputs require a security second pass.
- TASK-085 records and approves the operator's lab-open startup/autostart
  request.

### Events And Metrics

- `validate_events.py` reports canonical event shape and tolerates historical
  aliases as warnings.
- Current known historical event status: 0 validation errors and 33 expected
  historical warnings before normalization.
- Events are still append-only collaboration history. Do not rewrite old event
  lines just to clean warnings.

### Agent Status And Reconciliation

- `agents/status.json` was reconciled against hcom reality during TASK-082.
- Capability identities such as `codex` and `claude` are distinct from live
  hcom sessions such as `codex-lab-limo` and `claude-lab-rose`.
- `reconcile_agents.py` is available for checking durable state against hcom
  live state.
- `declare_standby.py` is the safe way for an agent to say its queue is empty:
  it writes SQLite first and exports the status mirror.

### Rise & Shine

- TASK-080 introduced the RnS watcher for recorded `out_of_tokens` reset times.
- TASK-083 upgraded RnS to handle hard silent stops with no final turn:
  transcript reset-time extraction, capped visible probes, incident tracking,
  and no headless resumes.
- TASK-084 added declared-idle handling:
  - declared standby suppresses check-ins;
  - hcom `listening` agents idle for 2+ hours with no claim get a message-only
    "is there something you should be doing?" check-in;
  - hcom `blocked`, `waiting`, active, non-live, claimed, and non-available
    states are suppressed;
  - check-in events are attributed to TASK-084.
- Watcher tests reached 14/14 after TASK-084; full MAP suite reached 22/22.

### Emergence System

- Emergence records now have a clearer lifecycle: insight, synthesis, idea,
  experiment, promotion.
- SYN-0001 is the first real synthesis record: "two readers, one truth."
- IDEA-0007 is the canonical declared-idle check-in idea.
- IDEA-0008 was marked superseded by IDEA-0007 to avoid duplicate concepts.
- PROMO-0006 approved the declared-idle check-in work that became TASK-084.
- `map_emergence.py validate` and `map_emergence.py stale` were clean after the
  TASK-084 rework.

### Full-Report Closure

- TASK-082 closed the full-report coverage pass by refreshing the state picture,
  reviewing unresolved findings, and tying follow-up work into durable files.
- `MAP_System/artifacts/reviews/full-report-coverage-matrix-2026-07-02.md`
  is the best single artifact for tracing audit findings to closure.
- `MAP_System/artifacts/reports/MAP-system-full-report-2026-07-02.md` remains
  the larger narrative report.

## Important Artifacts

- Restart/startup note:
  `MAP_System/notes/command-center-lab-restart-startup.md`
- RnS protocol:
  `MAP_System/notes/limit-exhaustion-protocol.md`
- Current state:
  `MAP_System/shared/current-state.md`
- Decisions:
  `MAP_System/shared/decisions.md`
- Canonical repo decision:
  `MAP_System/shared/canonical-repo.md`
- TASK-083 review:
  `MAP_System/artifacts/reviews/task083-rereview.md`
- TASK-084 review:
  `MAP_System/artifacts/reviews/task084-rereview.md`
- TASK-085 autostart task:
  `MAP_System/tasks/TASK-085.json`

## Known Residue

- `Projects/` is untracked in the canonical repo and should be treated as
  unrelated/private unless the operator asks for Pathwell work.
- Historical event warnings remain until a future normalization task runs.
- The old stale archive can be deleted later only after the operator confirms
  it is no longer needed.
- Older low-priority backlog remains for `aider_wrapper.py`,
  `local_runner.py`, and a synthesis CLI flag mismatch.
- Autostart launcher files are outside Git. Current expected behavior is
  documented in `MAP_System/notes/command-center-lab-restart-startup.md` and
  reviewed in `MAP_System/artifacts/reviews/task085-review.md`.

## Restart Checklist

After reboot or a full lab close/open:

1. Open AI Command Center Lab.
2. Confirm visible Codex and Claude lab tabs appear.
3. Confirm RnS starts or is already running.
4. Confirm each agent sends one startup orientation message to `@bigboss`.
5. If any part fails, use the manual fallback in
   `MAP_System/notes/command-center-lab-restart-startup.md`.

The key safety rule is unchanged: the lab may wake agents and ask for
orientation, but task work still follows MAP ownership, review, and approval
rules.
