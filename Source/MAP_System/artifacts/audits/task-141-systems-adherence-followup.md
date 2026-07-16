# TASK-141 Systems-Adherence Follow-up

task_id: TASK-141
owner: claude-lab-vino
date: 2026-07-04
scope: which of MAP's ~15 documented systems are genuinely exercised vs
specification-only, as a follow-up to TASK-129/130's audit; split with
codex-lab-neko (TASK-140 covers operating-loop/mechanics)

## Baseline

This does not repeat the full systems inventory from
`artifacts/audits/task-129-map-system-adherence-audit.md` and
`artifacts/audits/task-130-map-systems-real-usage-evidence.md`. Their
per-system usage table (Self-Repair/Risk/Change-Control/Emergence
genuinely used; Research/Context/Human-Interface/Archive-Retention
specification-only; Retrospective/Decision-Authority used once/thinly)
is treated as still current — nothing in the time since has changed
those systems' usage pattern. This follow-up instead checks two things
TASK-129/130 didn't verify: (1) whether their own two concrete
recommendations were actually acted on, and (2) whether their claims
about which systems have atomic-safe tooling were themselves correct.

## Finding 1: TASK-129's Finding 2 recommendation was never built (still open)

TASK-129 recommended a `map_repair.py` ID-allocation helper. It does not
exist. `repairs/` still allocates `REPAIR-NNNN`/`HEALTH-NNNN` by hand.
Logged as still-open in `shared/improvement-backlog.md` (updated this
task with a cheaper implementation path — see Finding 2).

## Finding 2: `map_emergence.py`'s ID allocation was not actually atomic (new, previously mis-assumed safe)

TASK-129's Finding 2 stated `repairs/` lacked atomic ID allocation
"unlike `map_task.py create --task-id auto` **or `map_emergence.py`'s ID
assignment**" — implying the latter was already safe. It was not:
`next_id()` is a plain scan of existing filenames with no lock at all,
the same failure shape as the `REPAIR-0001` collision, just never
observed in `emergence/` because it hadn't collided yet.

Verified by reproduction, not just re-reading the code: 8 concurrent
`map_emergence.py insight` calls against a temp copy of the repo produced
23 files but only 20 unique IDs (3 real collisions) with the
pre-existing code. The same test against a fixed version produced 23
files, 23 unique IDs, 0 collisions.

Fixed directly (bounded, mechanical, matches TASK-129's own "small,
mechanical, prevents a concrete recurring failure mode" criterion for
building immediately rather than just proposing): a per-artifact-kind
`fcntl.flock` around ID allocation + existence-check + write in
`create_artifact()`. Full record: `repairs/REPAIR-0005-emergence-id-allocation-race.md`.

This means TASK-129's own audit — despite being unusually rigorous about
independent verification for everything else it checked — carried one
unverified assumption forward. Worth naming as its own small lesson: even
audits that split work across independent agents and require re-runs can
still repeat a claim from documentation/memory without checking it
against the actual code, if no task specifically targets that claim.

## Finding 3: Retrospective cadence gap (partially closed)

TASK-129 recommended a lighter Retrospective cadence gate since
`RETRO-0001` (embedded in `RETROSPECTIVE_SYSTEM.md` itself, not a
standalone record) had no successor despite a full new phase (this
session's TASK-135-139 ProjectUpdater/CommandCenterUI integration cycle)
completing since.

This task files that successor: `retros/RETRO-0002-projectupdater-commandcenterui-integration-cycle.md`,
the first standalone (non-embedded) retrospective record, and documents
`retros/` as the intended folder for `RETRO-0002` onward in
`RETROSPECTIVE_SYSTEM.md`. This closes the "no successor" half of the gap
but not the "should there be a lighter mechanical cadence gate" half —
that remains a judgment call for the operator (forcing a retro after
every task risks the box-ticking-ceremony failure mode DEC-026 already
warned against for Emergence), not something this task decided
unilaterally.

## Finding 4 (process note, not a system-adherence finding): task-graph output-path drift, reproduced live and fixed at the tool level

While filing this task, a manual edit to `TASK-141.json`'s
`output_paths` (adding `MAP_System/retros/`) was silently reverted back
to the stale SQLite-held value at least twice, each time after an
unrelated `map_task.py approve` call for a different task ran a mirror
export. This is the exact drift class TASK-140's audit (gap #1)
independently found the same session, from a different angle (claim vs
file state after `claim_task()`). Between the two, this is now corroborated
from two directions in one session, not a one-off.

Root cause: `map_task.py` had no command to add an output path to an
existing task — `output_paths` could only be set at `create` time.
Hand-editing the file mirrors instead of the database was the only
option, and any later `sync_files()` call (triggered by an unrelated
task's `approve`/`create`) overwrote that edit back to what the database
still held. A raw-SQL edit to work around this was attempted and
correctly blocked as an unauthorized bypass of `map_task.py`.

Fix applied: added a new `map_task.py add-output-path <task_id> --path
<path> --actor <name>` subcommand, following the same
connect/ensure_agent/append_event/sync_files pattern already used by
`create`/`approve`/`rework`. Used it to durably register
`MAP_System/retros/` on TASK-141 through the sanctioned tool rather than
by hand-editing a mirror file. `validate_task_graph.py` passes with the
updated output_paths.

codex-lab-neko's rereview caught that the first version of this command
had no task-state guard: it would silently accept adding an output path
to a `RELEASED` (or any terminal) task, reproduced against a temp DB. Fixed
by restricting `add-output-path` to `NEEDS_SHAPING`/`READY`/`IN_PROGRESS`/
`CHANGES_REQUESTED` and rejecting `SUBMITTED`/`APPROVED`/`RELEASED`/`DONE`/
`RETIRED` with a clear error naming the actual status. Added
`tests/test_map_task_add_output_path.py` (success on an editable task,
rejection on `RELEASED` and on `SUBMITTED`) wired into `run_tests.sh`.

## Systems still specification-only (unchanged from TASK-130)

Re-checked quickly, no new evidence either way since TASK-130: Research,
Context, and Human-Interface remain documented-and-validator-backed but
unexercised — no real Research Brief/Context Packet/dashboard consumer
exists yet, and no task in this session's cycle needed one. Consistent
with TASK-129's own recommendation not to force these into existence
where the honest answer is "not needed yet."

## What's genuinely working (reinforcing, not just repeating TASK-129/130)

- Security second-pass review is now a live habit, not just a documented
  convention: TASK-135 and TASK-139 (both network-facing/write-capable)
  each got an explicit CSRF/injection/trigger-surface check before
  approval, unprompted by any gate.
- The no-self-review rule is being followed even when inconvenient
  (TASK-137, this session), and the resulting routing gap was turned into
  a durable fix the same day (TASK-138) and exercised again immediately
  after (helper `bula`).
- Independent review is holding to a real evidence bar: every review this
  session (TASK-135/136/138/139/140) involved live verification (curl
  against a running server, reproduced race conditions, re-run test
  suites) rather than trusting the submitter's claims at face value.

## Verification

```text
map_emergence.py validate: OK, 38 artifacts checked
map_emergence.py race reproduction (before fix): 8 concurrent creates -> 3 collisions
map_emergence.py race reproduction (after fix): 8 concurrent creates -> 0 collisions
python3 MAP_System/tests/test_map_emergence.py: 4/4 PASS
validate_repair_artifacts.py: PASS
validate_task_graph.py: PASS
validate_events.py: errors=0, warnings=33 (unchanged baseline)
full MAP suite (scripts/run_tests.sh): pass=33 fail=0 total=33
map_task.py add-output-path TASK-141 --path MAP_System/retros/ --actor claude-lab-vino: registered, validate_task_graph.py still passes
test_map_task_add_output_path.py: 3/3 PASS (editable-state success, RELEASED rejection, SUBMITTED rejection)
full MAP suite after status-guard fix (scripts/run_tests.sh): pass=34 fail=0 total=34
```

## Related records

- `MAP_System/artifacts/audits/task-129-map-system-adherence-audit.md`
- `MAP_System/artifacts/audits/task-130-map-systems-real-usage-evidence.md`
- `MAP_System/artifacts/reports/task-140-process-use-audit.md` (codex-lab-neko, complementary operating-loop angle)
- `MAP_System/repairs/REPAIR-0005-emergence-id-allocation-race.md`
- `MAP_System/retros/RETRO-0002-projectupdater-commandcenterui-integration-cycle.md`
- `MAP_System/shared/improvement-backlog.md` (map_repair.py item, updated with a cheaper implementation path)
