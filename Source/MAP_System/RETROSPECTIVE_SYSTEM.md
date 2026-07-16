<!-- hpom: file: RETROSPECTIVE_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-118 build, Guidelines/MAP_repo_systems_gap_review.md -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Retrospective / Learning System

Status: active
Decision: DEC-025
Owner: command-center
Built by: TASK-118

## What this is

This is the last system named in
`Guidelines/MAP_repo_systems_gap_review.md`. The improvement backlog and
Emergence already capture individual findings; this file adds the
cadence that reviews a completed cycle of work as a whole and asks
whether a repeated pattern should become permanent — a validator,
template change, or decision — rather than being re-discovered each time.

## Core principle

```
Every repeated failure should become a process improvement, validator, template change, or decision.
```

## The retrospective loop

Use `templates/RETROSPECTIVE_TEMPLATE.md` at the close of a work cycle
(a task sequence like a gap-review build, a project phase, or a fixed
cadence if the operator sets one). Answer, in order:

1. What worked? — worth reinforcing, not just skipping past.
2. What failed? — concrete, not vague.
3. What caused rework? — review round-trips, resubmissions, reverted edits.
4. What did agents misunderstand? — a rule, a file's purpose, a boundary.
5. What rules were unclear? — where documentation had to be re-read or
   caused a wrong first attempt.
6. What should become a validator, template change, or decision? — the
   output that actually prevents recurrence.

Save each completed record as a standalone file at
`MAP_System/retros/RETRO-NNNN-<slug>.md` (sequential, one shared counter
across all retrospectives) rather than embedding it in this system file.
A dedicated folder, not `repairs/`, because `validate_repair_artifacts.py`
only recognizes `REPAIR`/`HEALTH` filename prefixes and rejects anything
else placed in `repairs/` as an unknown artifact. `RETRO-0001` below
predates this convention and stays embedded as the worked example this
system was built from; `RETRO-0002` onward lives in `retros/`.

## Retrospective vs. Self-Repair

`SELF_REPAIR_SYSTEM.md`'s Follow-Up Prevention section already runs this
discipline at incident scale — one repair, checked for recurrence,
proposing a fix if it repeats. The Retrospective System runs the same
discipline at cycle scale — looking across many incidents/tasks at once,
where a pattern might not be visible from any single Repair Record.

```
Self-Repair: did this specific drift recur? → prevent per-incident.
Retrospective: looking at the whole cycle, what patterns recurred across many incidents/tasks? → prevent at the process level.
```

## Worked example: retrospective on TASK-103 through TASK-117

This is the first retrospective run under this system, covering the
gap-review build sequence that created the Research, Self-Repair,
Context, Decision/Authority, Human Interface, Risk, Security/Permissions,
Change Control, Project Bootstrapping, and Archive/Retention systems.

**What worked:**

- Splitting scope upfront with codex-lab-dino (prose/architecture to
  Claude, tooling/validators to Codex per `shared/hpom.md`'s default
  assignment rules) avoided duplicate work across the whole sequence.
- Registering `depends_on` between sequential tasks that shared
  `shared/decisions.md` (e.g., TASK-108 depends_on TASK-107) correctly
  prevented output-path collisions once it became routine.
- Requiring a full validator run (`validate_shared_state`,
  `validate_decisions`, `validate_task_graph`,
  `test_exporter_invariants.py`, `run_tests.sh`) before every submission
  caught real problems before they reached review, not after.

**What failed / caused rework:**

- TASK-103's first submission had a mirror-sync gap (SQLite said
  `SUBMITTED`, file mirrors still said `IN_PROGRESS`) and missing
  output_paths for shared/index files it had touched — one full
  rework/resubmit cycle.
- TASK-107's first submission referenced a nonexistent file
  (`notes/AGENTS.md`) — one rework/resubmit cycle.
- The output_paths-for-cross-linked-files gap recurred as a near-miss
  across TASK-111, TASK-112, TASK-115, and TASK-117: each time, the
  cross-link edits (adding backlinks in other systems' files) were made
  before the paths were registered in SQLite, and codex-lab-dino caught
  it with a proactive heads-up before submission each time, so it never
  reached actual review as a finding after TASK-103/107. By TASK-108,
  TASK-110, and TASK-114, paths were registered upfront without needing a
  heads-up — the pattern was being internalized mid-cycle, but not fast
  enough to stop recurring entirely.

**What agents misunderstood / what rules were unclear:**

- The exact moment "output_paths must include this file" applies was not
  obvious from `notes/task-authoring-guide.md` alone until the recurring
  near-miss made it concrete: any file touched by an Edit call, including
  a one-line backlink addition in another system's doc, counts as an
  output path, not just the primary deliverable files named in the task
  title.

**What should become a validator, template change, or decision:**

- Template change (applied in this same task): added a line to
  `notes/task-authoring-guide.md`'s Output Paths section stating
  explicitly that *any* file touched by an Edit/Write call — including a
  one-line cross-link backlink in another system's file — must be in
  `output_paths` before submission, not just the task's named
  deliverables. This directly prevents the TASK-111/112/115/117 pattern
  from recurring in the next cross-linking build sequence.
- No validator change needed: `validate_task_graph.py`'s collision
  detector already does its job correctly (it is what made the gap
  visible each time); the gap was in when agents registered paths
  relative to when they edited files, not in the validator's logic.

This finding is logged in `shared/improvement-backlog.md` per the
Relationship rules below.

## Relationship to other systems

```
Self-Repair prevents recurrence at incident scale.
Emergence captures the recurring pattern as an insight if it is novel enough.
Improvement backlog holds the finding until the permanent fix lands.
Change Control treats the permanent fix (validator/template change) as a normal change once approved.
```

- **`SELF_REPAIR_SYSTEM.md`**: a retrospective finding that is really just
  a repeated `DRIFT`/`BLOCKING` repair should already have Repair Records;
  the retrospective's job is to notice the repair records cluster into one
  pattern, not to re-litigate each incident.
- **`emergence/README.md`**: if a retrospective finding is genuinely novel
  (not just "we already knew this"), capture it as an `INS-NNNN` insight so
  it goes through normal promotion discipline rather than being silently
  acted on.
- **`shared/improvement-backlog.md`**: retrospective findings that need a
  permanent fix but are not urgent enough to action immediately are logged
  here, same as any other known-but-not-yet-fixed improvement.
- **`CHANGE_CONTROL_SYSTEM.md`**: once a retrospective's proposed
  validator/template/decision fix is approved, applying it is a normal
  change — reviewed, released, recorded — not a special retrospective-only
  path.

## When to run a retrospective

- At the close of a multi-task build sequence like this one.
- At the close of a project phase.
- On operator request at any time.
- Not after every single task — that duplicates Self-Repair's per-incident
  discipline and adds noise without adding signal.

## Related files

- `retros/` — standalone retrospective records (`RETRO-0002` onward)
- `templates/RETROSPECTIVE_TEMPLATE.md` [[RETROSPECTIVE_TEMPLATE]] — the retrospective record template
- `SELF_REPAIR_SYSTEM.md` [[SELF_REPAIR_SYSTEM]] — incident-scale prevention this system
  complements at cycle scale
- `emergence/README.md` [[emergence/README]] — where a novel retrospective finding becomes an
  insight
- `shared/improvement-backlog.md` [[improvement-backlog]] — where retrospective findings needing
  follow-up are tracked
- `CHANGE_CONTROL_SYSTEM.md` [[CHANGE_CONTROL_SYSTEM]] — where an approved retrospective fix is
  applied as a normal change
- `Guidelines/MAP_repo_systems_gap_review.md` — the gap review that
  identified this system as the last secondary gap, and whose own build
  sequence is this system's first worked example
