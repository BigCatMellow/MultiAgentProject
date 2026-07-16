<!-- hpom: file: CHANGE_CONTROL_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-114 build, Guidelines/MAP_repo_systems_gap_review.md -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Change Control System

Status: active
Decision: DEC-022
Owner: command-center
Built by: TASK-114

## What this is

MAP already has normal Git, `scripts/map-git`, `scripts/git_operation_lock.py`,
canonical repo decisions, and a release-path smoke checklist. This file
formalizes the pieces that were still informal: change request format,
release records, rollback notes, changelog policy, diff review
requirement, migration notes, version tags, and artifact retirement.

The gap-review-driven build of TASK-103 through TASK-114 is itself the
worked example this system documents: every one of those tasks produced a
release checklist in `artifacts/releases/` before being marked `RELEASED`.

## Core principle

```
Every change should be reviewable, attributable, and reversible until it is released.
```

## Change request format

A change request is not a new artifact type — it is a normal MAP task
(`tasks/TASK-NNN.json`) with `output_paths` naming exactly what changes.
Nothing here requires a separate change-request document; the task file
already is the change request once it has a title, description,
output_paths, and acceptance_criteria per
`notes/task-authoring-guide.md`.

## Diff review requirement

- Every task's changes are reviewed before `APPROVED`, per the existing
  Review Gate (`AGENTS.md`, `scripts/validate_review.py`) — this system
  does not add a new gate, it names the existing one as the diff-review
  requirement.
- No-self-review still applies (`db/claims.py` `claim_block_reason()`).
- A reviewer should be able to answer, from the review record alone: what
  changed, why, and what was verified — the existing review template
  already asks this.

## Release records

A release record is `scripts/release_task.py`'s checklist file under
`artifacts/releases/task-NNN-release-checklist.md`. Required contents,
already established by convention across TASK-101 through TASK-112, plus
Emergence capture per DEC-026/TASK-126:

- header naming task_id, released_by, release_date, review_record;
- a checklist of shared-file updates, decisions, follow-ups, event log
  completeness, **and Emergence capture considered**;
- a summary of what was delivered and why;
- a verification block naming every validator/test run and its result.

This system formalizes that convention as required, not optional, for any
task whose output touches `shared/`, `templates/`, or another system's
canonical file.

## Emergence capture is mechanically required, not a suggestion

Per DEC-026: an entire project (ProjectUpdater, TASK-123–125) shipped
without a single Emergence artifact even though real insights surfaced
during the build, because nothing required checking. `scripts/release_task.py`
now requires a literal `- [x] Emergence capture considered` line in every
release checklist, alongside the three checklist items already required
(shared-file updates, decisions recorded, follow-up tasks created) — see
`REQUIRED_CHECKS` in that script. A checklist can honestly say "considered,
nothing worth capturing"; the gate blocks release only when the line is
missing entirely, not when the answer is "no."

This applies to every project, not just MAP-system-level work — see
`PROJECT_BOOTSTRAPPING_SYSTEM.md`'s Emergence capacity requirement and
`NEW_PROJECT_WIZARD.md` step 9.

## Rollback notes

- Every release record should state whether the change is reversible by
  normal means (supersede a decision, `git revert`, rework a task) or
  requires special rollback steps (e.g., restoring a backup, as required
  before the upcoming folder-structure self-application review per hcom
  #19897).
- If a change is not cleanly reversible, that is itself a `STRUCTURAL`-
  severity, `DATA`-class risk per `RISK_SYSTEM.md` and should be logged,
  with the rollback plan stated before the change is made, not after.
- A repair that turns out to be the wrong fix rolls back through
  `SELF_REPAIR_SYSTEM.md`'s own record trail (supersede the Repair Record,
  do not silently re-edit it).

## Changelog policy

- MAP-system-level changes are already changelogged by
  `shared/decisions.md` (what changed and why) plus `events/events.jsonl`
  (when and by whom) — this system does not require a third,
  duplicate changelog file at the MAP-system level.
- Project-level work may keep a `Projects/<PROJECT_NAME>/changes/CHANGELOG.md`
  if the project is user-facing and benefits from a human-readable summary
  distinct from the decision log; this is optional and project-scoped.

## Migration notes

- Any change that requires re-running an exporter, re-claiming a task, or
  otherwise transitioning existing state (e.g., `migration/export_to_files.py`
  after an output_paths correction) should say so explicitly in the
  release record's verification block, not just in chat/hcom.
- A migration that changes the shape of durable data (new required field,
  new table, new file format) is at least an `ARCHITECTURE`-class decision
  per `DECISION_CLASSES.md` and should be recorded as such before agents
  rely on the new shape.

## Version tags

MAP does not currently version-tag individual releases; task IDs
(`TASK-NNN`) and decision IDs (`DEC-NNN`) already provide stable,
sequential identifiers for any given change. Introducing a separate
version-tag scheme is deferred — it would duplicate an identifier that
already exists, which `notes/documentation-style-guide.md`'s Pushback
Notes already discourages ("duplicate an existing guide" applies equally
to duplicating an existing identifier scheme). Revisit only if MAP starts
shipping externally-versioned artifacts (e.g., a packaged release).

## Artifact retirement rules

- A retired artifact (superseded decision, closed task, dismissed
  emergence idea) is marked as such in place — `Status: superseded`,
  `RETIRED` task status (see TASK-100), `DISMISSED` emergence status — not
  deleted.
- Retired artifacts stay in their original location; do not move them into
  `archive/` purely for being retired. `archive/` is for brain-compaction
  history per `notes/brain-compaction-guide.md`, a different lifecycle
  stage than "superseded but still in place."

## Relationship to other systems

```
Self-Repair fixes drift found after a change lands; rollback notes say how.
Decision/Authority governs approval for changes that are AUTHORITY/POLICY class.
Risk tracks a change that could not be cleanly rolled back.
Human Interface surfaces the review queue this system's diff-review requirement feeds.
```

- **`SELF_REPAIR_SYSTEM.md`**: when a repair is the correct response to a
  bad change, the Repair Record documents it; this system's rollback-notes
  rule is what should have been stated before the change, so the repair
  has something to follow.
- **`DECISION_AUTHORITY_SYSTEM.md`**: a change that is AUTHORITY or POLICY
  class per `DECISION_CLASSES.md` needs command-center approval before
  release, same as any other decision — Change Control does not add a
  separate approval ladder.
- **`RISK_SYSTEM.md`**: a change without a stated rollback plan, or one
  that turns out irreversible, is a `DATA`-class risk entry.
- **`HUMAN_INTERFACE_SYSTEM.md`**: the dashboard's review-queue section is
  exactly the set of changes awaiting this system's diff-review
  requirement.

## Related files

- `artifacts/releases/` — release records; TASK-101 through TASK-112's
  checklists are the worked examples this system formalizes
- `scripts/release_task.py` — the release-gate implementation, including
  the mandatory "Emergence capture considered" checklist requirement
- `emergence/README.md` [[emergence/README]] — what Emergence capture actually means, and the
  CLI for doing it
- `PROJECT_BOOTSTRAPPING_SYSTEM.md` [[PROJECT_BOOTSTRAPPING_SYSTEM]] — where new projects are required to
  set up Emergence capacity from day one
- `notes/review-guide.md` [[review-guide]] — the diff-review standard this system points to
- `ARCHIVE_RETENTION_SYSTEM.md` [[ARCHIVE_RETENTION_SYSTEM]] — the archiving lifecycle stage distinct
  from this system's retirement-in-place rules
- `RETROSPECTIVE_SYSTEM.md` [[RETROSPECTIVE_SYSTEM]] — where an approved retrospective fix is
  applied as a normal change through this system
- `SELF_REPAIR_SYSTEM.md` [[SELF_REPAIR_SYSTEM]] — where rollback-as-repair is recorded
- `HUMAN_INTERFACE_SYSTEM.md` [[HUMAN_INTERFACE_SYSTEM]] — where this system's diff-review
  requirement is surfaced as the dashboard's review-queue section
- `DECISION_AUTHORITY_SYSTEM.md` [[DECISION_AUTHORITY_SYSTEM]] — where AUTHORITY/POLICY-class changes
  are approved
- `RISK_SYSTEM.md` [[RISK_SYSTEM]] — where irreversible-change risk is tracked
- `Guidelines/MAP_repo_systems_gap_review.md` — the gap review that
  identified this system as a secondary gap
