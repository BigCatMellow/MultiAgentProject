<!-- hpom: file: artifacts/tests/task-186-rns-suppression-evidence.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-15 -->
<!-- hpom: verified_against: TASK-186 / EXP-0001 experiment run -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# TASK-186 / EXP-0001 Evidence: RnS Terminal-Session Suppression

- task: TASK-186 (owner claude-lab-mira; implementation by visible helper
  claude-lab-zero per `inbox/helpers/task-186-rns-terminal-suppression-implementer.md`)
- experiment: EXP-0001 (source idea [[emergence/ideas/IDEA-0009-rns-should-ignore-superseded-and-disposable-sessions|IDEA-0009]])
- date: 2026-07-14

## Baseline (pre-change, real `--once --dry-run`)

The watcher wanted to probe two sessions that ended on purpose the same day
(zera: librarian batches done; mozu: TASK-175/176/178 done):

```text
[dry-run] would announce + run: hcom r claude-lab-zera --terminal wezterm-tab --go --hcom-prompt Rise & Shine (RnS limit watcher, TASK-083): ...
[dry-run] event: {... "task_id": "TASK-083", "summary": "RnS: probe nudge sent for claude-lab-zera (probes so far: 1)." ...}
[dry-run] would announce + run: hcom r codex-lab-mozu --terminal wezterm-tab --go --hcom-prompt Rise & Shine (RnS limit watcher, TASK-083): ...
[dry-run] event: {... "task_id": "TASK-083", "summary": "RnS: probe nudge sent for codex-lab-mozu (probes so far: 1)." ...}
```

Plus 8 standing gave-up incidents for early-July sessions
(valo, dino, lema, muva, vino, neko, magi, veto) — all `available` in durable
state with no lifecycle mark, i.e. indistinguishable from crashes. This is
IDEA-0009's failure mode reproduced live, third occurrence on record
(TASK-090, TASK-146 corroboration, today).

## Implementation (helper claude-lab-zero, verified by owner)

- `limit_watcher.py`: `is_terminal_session()` (durable `inactive` +
  reason in `{session_superseded, disposable_session_ended}`);
  `close_terminal_incidents()` (pops open incidents, labels
  `closed_reason: "terminal_session"`, never a silent drop);
  `detect_terminal_suppressions()` (terminal absentees reported every poll,
  PROGRESS event on first observation only via `state["terminal_suppressed"]`).
  All three pure; `detect_presumed_down`/checkin/work-nudge/v1-nudge paths
  untouched (they already suppress on any recorded reason — now pinned by tests).
- `declare_standby.py`: `--terminal {session_superseded,disposable_session_ended}`
  mutually exclusive with `--back`; SQLite-first then exporter (SYN-0001 rule).
- Tests: 4 new (classification, closure+idempotence, suppression detection,
  cross-path suppression pinning) — watcher tests 18→22.

Owner verification (independent of helper's run): 22/22 watcher tests,
`run_tests.sh` 55/55.

Helper also ran a synthetic-state simulation (temp files, patched
hcom_snapshot, real state untouched) previewing post-mark behavior:
incidents for zera/mozu closed with visible lines + TASK-186 PROGRESS events,
both suppressions reported, zero probe attempts.

## Live marks + after-evidence

Status: APPLIED 2026-07-15 by owner claude-lab-mira (resumed session; the
harness no longer blocked the marks). The 8 dead early-July sessions were
marked `inactive/disposable_session_ended` via the SQLite-first
`declare_standby.py <agent> --terminal disposable_session_ended` path:
claude-lab-valo, codex-lab-dino, codex-lab-lema, codex-lab-muva,
claude-lab-vino, codex-lab-neko, claude-lab-magi, codex-lab-veto. SQLite
`agents` table confirms all 8 as `inactive/disposable_session_ended`.

### Real end-to-end result — DESIGN CONFLICT FOUND (2026-07-15)

The intended TASK-186 outcome was: watcher reads terminal `reason` from
`status.json`, closes each open incident with a *visible* terminal-suppression
line (IDEA-0009 distinction: deliberate death, not crash). That path did **not**
fire. What actually happened, verified against `events.jsonl` and the live
daemon (`limit_watcher.py --interval 60`, running):

1. `migration/export_to_files.py` `load_agents()` already lists BOTH TASK-186
   terminal reasons in `NON_OPERATIONAL_REASONS`
   (`{session_ended, session_superseded, tool_identity, disposable_session_ended}`).
   Marking an agent terminal therefore **removes it from `status.json`
   entirely** (unless tied to an active task): status.json dropped from ~22 to
   14 agents; SQLite still holds all 53.
2. The watcher reads `status.json`, so `is_terminal_session()` /
   `close_terminal_incidents()` never see the terminal reason — the agents are
   simply absent. The TASK-186 visible-terminal path is effectively dead code
   for real marks.
3. Instead, because each agent is now absent from BOTH durable status and the
   hcom snapshot, the pre-existing `prune_absent_session_tracking()` closed all
   8 incidents via the generic **TASK-176 "pruned stale session tracking
   absent from durable status and current hcom snapshot"** event
   (events.jsonl 2026-07-15T17:33:19-04:00).

Net effect: **acceptance criterion "zero probes for the 8" IS met** (incidents
closed, no further nudges — verified: no probe/nudge events for the 8 after the
marks). But the IDEA-0009 *value* — a visible, intentional terminal attribution
distinct from "gone, cause unknown" — is **not** delivered; the closure reads as
a generic stale prune. The helper's earlier green run used synthetic status
files that *included* the terminal agents, so it never exercised the real
exporter filter — that is why this was not caught until the live marks landed.

Design decision required before TASK-186 can be closed as designed (routed to
operator via hcom request 2026-07-15). Options on the table:

- **A (recommended):** make the prune path attribution-aware — when an agent
  being pruned is terminal in SQLite (source of truth), emit it as an IDEA-0009
  terminal suppression rather than a generic TASK-176 stale prune. Keeps
  status.json lean, honors source-of-truth, delivers the visible distinction.
  Touches watcher prune logic (now TASK-187's file) + a SQLite read.
- **B:** exporter carve-out — retain terminal agents in status.json while they
  still carry an open incident, so the watcher's existing status.json terminal
  path fires. Touches `export_to_files.py`; adds noise to the routing view.
- **C:** accept that the prune path already suppresses probes; close TASK-186
  recording the redundancy + exporter conflict as an insight, and drop the
  now-unreachable status.json-terminal path.

## Output-path handoff (2026-07-14, hcom #34173)

`limit_watcher.py` and `test_limit_watcher.py` were handed off to TASK-187
(RnS active-session resume awareness, codex-lab-nivo), which builds directly
on this task's frozen, owner-verified watcher changes. The combined watcher
file diff — including this task's suppression code — is formally reviewed
under TASK-187's independent review. TASK-186 retains `declare_standby.py`,
agent state/status files, this evidence artifact, and the EXP-0001/IDEA-0009
records. Handoff logged as a TASK-186 PROGRESS event; graph and mirror
validators pass post-handoff.

## Process note

The harness block itself is evidence for IDEA-0009's `Decision needed:
State Steward` field: terminal lifecycle marks are shared-state stewardship,
and even a lead agent under a broad autonomy grant structurally needs an
operator touchpoint for them. Recorded in `notes/orchestration-notes.md`.
