<!-- hpom: file: repairs/README.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-105 build -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Self-Repair — Quick Start

See `MAP_System/SELF_REPAIR_SYSTEM.md` for the full system definition,
severity levels, authority tiers, and follow-up prevention rules. This file
is the working quick-start for running a repair pass or filing a repair.

## When to run a health check

Run one when you suspect drift but have not yet located it: after a review
cycle that touched multiple files, after a session resumes from a
STATE_SNAPSHOT, or on a regular cadence if you are standing by with no
assigned task.

```bash
MAP_System/.venv/bin/python MAP_System/scripts/validate_shared_state.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_decisions.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_task_graph.py
MAP_System/.venv/bin/python MAP_System/scripts/validate_events.py
MAP_System/.venv/bin/python MAP_System/scripts/reconcile_agents.py
MAP_System/.venv/bin/python MAP_System/scripts/map_emergence.py stale
MAP_System/.venv/bin/python MAP_System/scripts/map_metrics.py
MAP_System/.venv/bin/python MAP_System/scripts/local_assistant_health.py
MAP_System/.venv/bin/python MAP_System/tests/test_exporter_invariants.py
```

Copy `MAP_System/templates/repairs/HEALTH_CHECK_REPORT_TEMPLATE.md` to
`MAP_System/repairs/HEALTH-NNNN-<slug>.md` and record what each check found.
A health check report is read-only — it does not fix anything by itself.

## When to file a repair

Once a health check (or any other observation) surfaces a `DRIFT`,
`BLOCKING`, or `STRUCTURAL` finding (see severity table in
`SELF_REPAIR_SYSTEM.md`):

1. Classify severity.
2. If `DRIFT` or mechanical `BLOCKING`: apply the fix, then copy
   `REPAIR_RECORD_TEMPLATE.md` to `MAP_System/repairs/REPAIR-NNNN-<slug>.md`
   and log what was found, fixed, and verified.
3. If `BLOCKING` requiring judgment or `STRUCTURAL`: draft the Repair
   Record with a proposed fix, post it via hcom `--intent request`, and
   wait for approval before applying.
4. Re-run the validator(s) that surfaced the issue, plus
   `validate_task_graph.py` and `test_exporter_invariants.py` if task/mirror
   state was touched, plus the full suite
   (`MAP_System/scripts/run_tests.sh`) if more than one subsystem changed.
5. If this is a repeat of a known drift class, check
   `shared/improvement-backlog.md` and propose a permanent fix (validator,
   template change, or decision) instead of only fixing this instance.

`scripts/map_repair.py` is the preferred way to create new repair records
because it allocates `REPAIR-NNNN` under a file lock:

```bash
python3 MAP_System/scripts/map_repair.py create \
  --repair-id auto \
  --found-by codex-lab-nivo \
  --severity DRIFT \
  --summary "What drift was found" \
  --surfaced-by "validator or review finding" \
  --fix "What changed or is proposed" \
  --verification "Checks rerun"
```

Use an explicit `--repair-id REPAIR-NNNN` only when preserving a known ID.
The allocator is intentionally file-lock based and does not use SQLite.

## Numbering

Use a shared sequence per record type: `REPAIR-0001`, `HEALTH-0001`.
Retrospective records (`RETRO-NNNN`, cycle-scale, see
`MAP_System/RETROSPECTIVE_SYSTEM.md`) are a separate record type with
their own folder (`MAP_System/retros/`) — `validate_repair_artifacts.py`
only recognizes `REPAIR`/`HEALTH` prefixes, so a `RETRO-NNNN` file placed
in this folder fails validation as an unknown artifact.

## Folder layout

```
MAP_System/
  repairs/
    README.md              ← this file
    REPAIR-NNNN-<slug>.md
    HEALTH-NNNN-<slug>.md
  retros/
    RETRO-NNNN-<slug>.md
  templates/repairs/
    REPAIR_RECORD_TEMPLATE.md
    HEALTH_CHECK_REPORT_TEMPLATE.md
  templates/
    RETROSPECTIVE_TEMPLATE.md
```

## What this does not replace

- It does not replace the review/release gates — a repair to your own
  in-flight task output still goes through normal review if the task is
  already under review.
- It does not replace `shared/decisions.md` — `STRUCTURAL` repairs still
  land there once approved.
- It does not replace the Research System — if the "drift" is actually a
  stale or contradictory fact rather than a state-mirror disagreement,
  route it through `RESEARCH_SYSTEM.md` first.
