<!-- hpom: file: artifacts/tests/task-186-rns-suppression-evidence.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
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

Status: PENDING OPERATOR ACTION. The harness permission layer blocks the
acting agent from batch-writing lifecycle marks for sessions it didn't create
(`declare_standby.py <agent> --terminal session_superseded` × 10). Operator
asked to run the one-line loop (hcom request 2026-07-14); on completion this
section gets the real post-change `--once --dry-run` output, which must show:

1. incident-closure lines for all marked agents with open incidents;
2. suppression lines for marked agents in `last_live`;
3. zero `hcom r` probe attempts for marked agents.

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
