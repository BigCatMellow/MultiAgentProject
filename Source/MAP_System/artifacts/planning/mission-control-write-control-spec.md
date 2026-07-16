# Mission-Control Write-Control Spec (TASK-168, Gap-Plan Increment 4)

Status: draft-active (design only)
Owner: command-center
Built by: TASK-168
Source: `mission-control-command-center-gap-plan.md` (increment 4)

## Purpose

Specifies how each of the mission-control TUI's 7 currently-disabled
intervention keybindings (`DISABLED_INTERVENTION_KEYBINDINGS` in
`scripts/mission_control_tui.py`) would eventually call a sanctioned MAP
command safely. **This task does not implement any of it.** Per the
gap-plan's explicit non-goal: "Do not add write-capable TUI actions before
the write-control design is reviewed." No code in `mission_control_tui.py`
or `_mission_control_app.py` is touched by this task.

## Design Principle (inherited, not invented here)

Every control below follows the same shape, already established by
`map-kill-switch-spec.md`'s "First Implementation Constraints" and
`SELF_REPAIR_SYSTEM.md`'s authority tiers: **the TUI is a client of
sanctioned commands, never a second writer.** It must never open `map.db`,
task JSON, `task_graph.json`, or `events.jsonl` for writing directly — every
action below is "call this existing CLI/function," full stop.

## The 7 Controls

### A — Approve selected submitted task

- **Sanctioned command**: `scripts/map_task.py approve <task_id> --reviewer <identity> --review-record <path>`
- **Precondition**: a review record must already exist at the path the TUI
  shows in the task's drilldown (TASK-166 output); the TUI never drafts
  the review record itself — that remains a core-agent judgment call, not
  a keypress.
- **Dry-run/preview**: show the task's acceptance-criteria checklist,
  which review record will be cited, and the reviewer identity that would
  be attributed (the identity running the TUI session).
- **Confirmation text**: `Approve {task_id} using review record {path} as {identity}? [y/N]`
- **Post-action validator**: `validate_task_mirrors.py` (already run
  internally by `map_task.py approve`); TUI re-fetches
  `build_dashboard_snapshot()` to confirm the task moved out of
  `submitted_tasks`.
- **Rollback**: approvals are not mechanically reversible from the TUI. A
  wrong approval requires a normal `CHANGE_CONTROL_SYSTEM.md` rollback note
  and a new decision entry — same as any other approval error, not a
  TUI-specific undo.

### R — Reject / request changes on selected submitted task

- **Sanctioned command**: `scripts/map_task.py reject <task_id> --reviewer <identity> --reason <text>` (or the review-record-driven CHANGES_REQUESTED path used throughout this session's own TASK-158/160/161/162/164 review cycles).
- **Dry-run/preview**: show the reason text the operator is about to submit; require it non-empty (mirrors this session's own repeated pattern of citing concrete findings, not a bare rejection).
- **Confirmation text**: `Reject {task_id} with reason "{reason}"? [y/N]`
- **Post-action validator**: `validate_task_mirrors.py`; confirm task status is `CHANGES_REQUESTED` and `claimed_by` is cleared.
- **Rollback**: `scripts/map_task.py rework` already exists as the sanctioned "undo a rejection was premature" path — the TUI would call that, not invent a new one.

### K — Kill or suspend a runaway agent/task

- **Sanctioned command**: this is the one control with no existing single
  CLI — it decomposes into two real, already-built primitives: (a)
  `scripts/halt_state.py set repair_only --scope task --target <task_id> --reason validator_blocking_anomaly --set-by <identity>` to stop further dispatch to that task, and (b) an hcom message to the owning agent
  using the operative 6-token MATOCP subset (`!ACK`/`!LGTM`/`!ERR`/`!REQ`/`!WARN`/`!NOTE`
  per `AGENTS.md` and `validate_protocol.py`'s explicit scope decision from
  TASK-162) — **correction from an earlier draft of this spec, which cited
  `!HALT` from the fuller 17-token `Guidelines/llm-communication-rules.md`
  spec; TASK-162's own protocol validator only recognizes the 6-token
  subset, so `!HALT` would fail protocol validation today (confirmed via
  `validate_protocol.py`'s review of this task).** The correct shape is
  `hcom send @<agent> --intent request -- "!REQ halt @ <task_id> reason=\"{reason}\""`
  — a well-formed `!REQ` asking the agent to stop, not a token the operative
  protocol doesn't recognize. If a dedicated human-interrupt token like
  `!HALT` is wanted later, that requires its own reviewed protocol-extension
  task (updating `AGENTS.md`'s Communication section and
  `validate_protocol.py`'s `MATOCP_TOKENS`) before this control could use it.
- **Precondition**: TUI must show which task/agent is selected and confirm
  it is actually flagged `broken` in the liveness roster (TASK-158's
  `shared/liveness-state.md`) — killing a merely `idle` agent is a policy
  violation this control must refuse, not just discourage.
- **Dry-run/preview**: show the halt record that would be written and the
  hcom message text verbatim before sending.
- **Confirmation text**: `Set repair_only halt on {target} and notify via hcom? [y/N]`
- **Post-action validator**: re-fetch liveness snapshot; confirm halt
  state via `halt_state.py show`.
- **Rollback**: `halt_state.py clear --cleared-by <identity> --clear-reason <text>` — already a sanctioned command (TASK-159), reused as-is.

### N — Resume/nudge selected agent

- **Sanctioned command**: `hcom r <agent> --terminal wezterm-tab` (the
  existing visible-resume convention this session used repeatedly, e.g.
  the RnS mechanism in `scripts/limit_watcher.py`) — **never** `--headless`,
  per this workspace's standing rule that resumes must be visible so the
  operator can see and respond to prompts.
- **Precondition**: agent must be in `idle` or `suspect` liveness state,
  not `broken` (that's control K's job) or `standby` (deliberate, do not
  nudge per `map-liveness-reaper-spec.md`'s explicit rule).
- **Dry-run/preview**: show the exact `hcom r` command that would run.
- **Confirmation text**: `Resume {agent} via visible wezterm-tab? [y/N]`
- **Post-action validator**: none needed beyond hcom's own launch
  confirmation; TUI re-fetches liveness snapshot on next refresh.
- **Rollback**: not applicable — a resume is not a state mutation to MAP's
  canonical store, only a live-session action; no rollback needed, per
  `CHANGE_CONTROL_SYSTEM.md`'s "no rollback needed, artifact-only" category
  (adapted here: no rollback needed, session-only).

### B — Bump budget

- **Status: BLOCKED/DEFERRED, not a callable control today.** Verified
  against the actual `scripts/cost_governance.py` CLI (`--help`): it only
  exposes accounting/spend-breaker inputs (`--budget-scope`,
  `--budget-key`, `--budget-limit`, token/cost recording) — there is no
  existing writer for an *approved override record*
  (`approved_by`/`old_limit`/`new_limit`/`expires_at`/`reason`) as
  `map-cost-governance-spec.md`'s "Operator Approval Path" describes.
  **Correction from an earlier draft of this spec**, which named this
  override path as a "sanctioned command," contradicting this spec's own
  cross-cutting requirement #5 that every named command must already
  exist. It does not yet.
- **Bounded interim behavior**: until that writer is built and reviewed,
  key `B` may only do one thing: emit a command-center approval **request**
  (an hcom `--intent request` message plus a `PROGRESS` event recording the
  requested scope/old_limit/new_limit/reason) — it must NOT write any
  budget or override state, because no sanctioned command exists to do so
  correctly (in particular, `map-cost-governance-spec.md`'s rule that "only
  command-center can approve AUTHORITY/POLICY-level budget increases" has
  no enforcement mechanism yet).
- **Precondition**: none beyond the request itself being well-formed and
  including a non-empty reason.
- **Dry-run/preview**: show current spend/limit (from
  `cost_governance.py`'s accounting output) and the requested new limit —
  read-only data the TUI already has, not a write.
- **Confirmation text**: `Send budget-override REQUEST for {scope}: {old_limit} -> {new_limit} to command-center? (no budget state is changed by this) [y/N]`
- **Post-action validator**: none — no state changed. The request is
  visible as a `PROGRESS` event and, once TASK-159's follow-on ships an
  actual override-record writer, as a pending item in the attention queue.
- **Rollback**: not applicable — a request-only action has nothing to roll
  back.
- **Prerequisite for the full control**: a follow-on task must add the
  override-record writer to `cost_governance.py` (or a new script) and get
  it reviewed before `B` can become a real budget-mutating control. This
  spec does not build that writer.

### O — Override false halt

- **Sanctioned command**: `scripts/halt_state.py clear --cleared-by <identity> --clear-reason <text>`, but ONLY after the finding has been adjudicated `false_positive` per `map-protocol-validator-spec.md`'s / `map-semantic-validator-spec.md`'s adjudication tables — this control is not a generic "clear any halt" button.
- **Precondition**: TUI must show the triggering validator finding
  (protocol or L1/L2) before allowing the override, and require the
  adjudicating identity to type the reason, which becomes the audit trail
  (per `map-validator-halt-state-spec.md`'s "False-Positive Path" rule:
  a false-positive clear is calibration data, not a repair, and must not
  be conflated with a real repair record).
- **Dry-run/preview**: show the validator's original finding text and the
  clear_reason about to be submitted.
- **Confirmation text**: `Adjudicate this as a FALSE POSITIVE and clear the halt? [y/N]`
- **Post-action validator**: `halt_state.py show` confirms `state=clear`; TUI logs this as calibration data per the spec (feeds judge-accuracy work, not `SELF_REPAIR_SYSTEM.md`'s repair-recurrence tracking).
- **Rollback**: none — a cleared halt that turns out to be a real defect after all is a new finding, not a rollback of the clear.

### D — Dead-letter replay

- **Sanctioned command**: `scripts/dead_letter_queue.py replay <dead_letter_id>` (TASK-161, already built and tested).
- **Precondition**: TUI shows the record's `replay_policy` first — only
  `return_ready` and `close_unreplayable` are safe for a single keypress;
  `create_repair_task`/`operator_decision` policies should route to
  "create the task" or "escalate," not silently call `replay()` (which,
  per TASK-161's own implementation, marks those as `blocked` rather than
  requeuing — the TUI's job is to make that distinction visible, not to
  paper over it with one generic "replay" action).
- **Dry-run/preview**: show `reason`, `attempt_count`, and `replay_policy`
  before acting.
- **Confirmation text**: `Replay {dead_letter_id} for {task_id} via policy={replay_policy}? [y/N]`
- **Post-action validator**: `dead_letter_queue.replay()` already runs
  `export_to_files.py` + `validate_task_mirrors.py` internally (TASK-161's
  own review-driven fix); TUI re-fetches `get_dead_letter_summary()`.
- **Rollback**: a task returned to `READY` by mistake is handled by the
  normal claim/lease lifecycle (nobody is forced to claim it); no special
  rollback path needed beyond that.

## Cross-Cutting Requirements (apply to all 7 controls)

1. **Every control requires an explicit confirmation keypress** (`y`),
   never a bare single-key action — this is a deliberate friction point,
   consistent with the whole 6.13 corpus's Principle 2 (gate irreversible
   actions behind a threshold with a safeguard, never a single check).
2. **Every control logs a canonical event** before and after the sanctioned
   command runs, so the causal chain is reconstructable from
   `events.jsonl` alone, not from TUI session memory.
3. **No control bypasses the identity it's attributed to** — the TUI must
   know which agent/operator identity is driving it (matching this
   session's own hcom-identity conventions) and pass that through as
   `--reviewer`/`--cleared-by`/`--set-by`/etc., never a generic "tui" actor.
4. **Every control is disabled by default** until this spec is reviewed
   and a follow-on implementation task explicitly enables it — this task
   produces the design, not a feature flag to flip.
5. **No control introduces a new write surface** — every "sanctioned
   command" named above already exists in this repo as of this task; if a
   future control needs a command that doesn't exist yet, that command
   must be designed and reviewed on its own before the TUI calls it.

## Implementation Sequencing (for a future task, not built here)

Recommended order if/when this spec is approved for implementation:

1. **N (resume/nudge)** — lowest risk, no canonical-state mutation.
2. **D (dead-letter replay)** — already fully sanctioned and tested by TASK-161; the TUI only adds a confirmation UI around an existing safe call.
3. **A/R (approve/reject)** — well-understood, high-value, existing commands; requires the review-record precondition to be enforced in the UI, not just documented.
4. **O (override false halt)** — requires careful UI to avoid conflating "clear" with "the defect wasn't real."
5. **K (kill/suspend)** — requires the liveness precondition check built first.
6. **B (budget bump)** — blocked on TASK-159's cost-governance implementation shipping the override-record writer function first.

## Related Files

- `MAP_System/scripts/mission_control_tui.py` (`DISABLED_INTERVENTION_KEYBINDINGS`)
- `MAP_System/artifacts/planning/mission-control-tui-spec.md` [[mission-control-tui-spec]]
- `MAP_System/artifacts/planning/map-kill-switch-spec.md` [[map-kill-switch-spec]]
- `MAP_System/artifacts/planning/map-validator-halt-state-spec.md` [[map-validator-halt-state-spec]]
- `MAP_System/artifacts/planning/map-cost-governance-spec.md` [[map-cost-governance-spec]]
- `MAP_System/scripts/dead_letter_queue.py`
- `MAP_System/CHANGE_CONTROL_SYSTEM.md` [[CHANGE_CONTROL_SYSTEM]]
- `MAP_System/artifacts/planning/mission-control-command-center-gap-plan.md` [[mission-control-command-center-gap-plan]]
