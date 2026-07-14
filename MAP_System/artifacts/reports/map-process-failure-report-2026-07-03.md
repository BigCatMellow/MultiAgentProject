# MAP Process Failure Report: Self-Update / Gap-Fill Cycle

task_id: TASK-122
owner: codex-lab-dino
date: 2026-07-03
scope: TASK-103 through TASK-121, with supporting evidence from current
TASK-122 state checks
emphasis: what went wrong, what is missing, and what still depends on manual
attention

## Summary

The MAP self-update cycle produced the requested systems, validators, health
checks, retrospective loop, backup, and folder cleanup. The important negative
finding is that the system succeeded by relying heavily on active reviewers to
notice drift, incomplete ownership records, stale references, and workflow
semantic mismatches.

The MAP now has more process surface area than it can automatically enforce.
The next work should not be more prose policy first. It should be enforcement
and reconciliation: diff-to-output-path checks, mirror-vs-SQLite checks,
cross-link freshness checks, event-log normalization, reviewer/release handoff
locking, and a clearer bridge between universal `Guidelines/` and MAP-specific
operating rules.

## Inputs Accounted For

- `claude-lab-valo` sent a findings packet via hcom #21527. Incorporated:
  recurring output-path gaps, missing mid-cycle retrospective, duplicate
  validator placeholder bug, missing canonical risk register, stale emergence,
  spec-only Human Interface, lack of standalone retrospective storage, untested
  project wizard, and fragmented tooling visibility.
- `claude-lab-sara` sent a findings packet via hcom #21535. Incorporated:
  cross-link staleness, repeated output-path under-registration, TASK-103
  SQLite/file drift, TASK-116 runner semantic drift, TASK-120 shipped-validator
  bug discovery, and the broader missing automation theme.
- `codex-lab-muva` sent a findings packet via hcom #21539. Incorporated:
  source-of-truth drift, output-path ownership misunderstanding, validation
  arriving after systems, terminal-status drift, noisy live/durable agent
  reconciliation, stale cross-link wording, and retrofit-policy ambiguity.
- `codex-lab-lema` explicitly stood down from duplicate report ownership and
  offered review/contribution via hcom #21491/#21493, then sent a findings
  packet via hcom #21603. Incorporated/covered: output-path timing gaps,
  mirror-sync fragility, TASK-116 status-semantics overgeneralization,
  TASK-119 stale-claim/RnS flow gap, TASK-118 cross-system prose drift,
  TASK-120 health-check discoveries, and broadcast ownership ambiguity.

## Main Failure Pattern

MAP's process was good enough to catch many defects before final release, but
not early enough and not automatically enough. The system repeatedly depended
on a reviewer remembering rules that were not yet enforced by tooling.

That matters because this self-update was exactly the kind of work MAP is meant
to handle: many agents, many cross-linked files, multiple state stores, and a
sequence of dependent tasks. If MAP only stays correct when one or two agents
carry the full context in working memory, it is not yet fully self-governing.

## What Went Wrong

### 1. State mirrors still drifted from SQLite

TASK-103 first reached review with SQLite reporting `SUBMITTED` while the task
JSON and task graph still showed `IN_PROGRESS`. The review record
`MAP_System/artifacts/reviews/task103-review-dino.md` required rework, and the
re-review confirmed the mirrors were corrected.

The same class is still observable in the current reporting task: while working
TASK-122, `map_task.py log TASK-122` and the runner knew the task was
`IN_PROGRESS`, but `MAP_System/tasks/TASK-122.json` still showed `READY` before
an explicit export/sync pass.

Missing process support:

- a submit/claim/release wrapper that guarantees file mirrors are exported;
- a validator that fails when SQLite, task JSON, and task graph disagree;
- a review gate that treats mirror drift as a first-class preflight failure,
  not a reviewer-discovered defect.

### 2. Output-path ownership rules were not internalized

TASK-103 omitted changed shared/index files from `output_paths`:
`MAP_System/shared/decisions.md`, `MAP_System/shared/current-state.md`, and
`MAP_System/templates/README.md`. That was corrected after review.

The same pattern continued as near-misses across TASK-111, TASK-112, TASK-115,
and TASK-117. RETRO-0001 in `MAP_System/RETROSPECTIVE_SYSTEM.md` records that
one-line cross-link and backlink edits were repeatedly treated as incidental
instead of as owned outputs.

TASK-118 added guidance to `MAP_System/notes/task-authoring-guide.md`, but this
is still guidance, not enforcement.

Missing process support:

- a diff-vs-output-path validator;
- a pre-submit helper that lists edited files not registered as outputs;
- a rule that shared/backlink/index edits are never "incidental" for task
  ownership purposes.

### 3. Cross-link staleness was caught manually

TASK-107 referenced a nonexistent `MAP_System/notes/AGENTS.md` as canonical
authority. TASK-118 was submitted with `MAP_System/SELF_REPAIR_SYSTEM.md` still
describing the Retrospective System as "future" after DEC-025 adopted it in the
same task.

These were caught by review, not by an automated consistency check.

Missing process support:

- a stale-link validator for MAP-internal paths;
- a "future/planned/proposed" wording check when a system is adopted;
- a system-adoption checklist that verifies sibling documents move from future
  tense to current tense.

### 4. Validation often arrived after the system it should protect

The cycle repeatedly built prose/system contracts first, then validators in a
follow-on task:

- TASK-103 Research System, then TASK-104 validator;
- TASK-105 Self-Repair System, then TASK-106 validator;
- TASK-107 Context System, then TASK-109 validator;
- Risk System documents, then TASK-113 risk validator.

That sequencing is sometimes reasonable, but it left the first implementation
pass dependent on human review instead of mechanical gates.

Missing process support:

- a default "contract plus minimum validator" pattern for governance systems;
- explicit acceptance criteria that state which invariants must be enforced
  immediately and which may be deferred;
- a temporary risk flag when a system is released before its validator exists.

### 5. Runner/task semantics drifted despite existing policy

TASK-116 fixed the runner so `RELEASED` dependencies satisfy downstream tasks.
The first pass also made `RETIRED` dependency-satisfying, which violated the
TASK-100 terminal-status policy. `MAP_System/artifacts/reviews/task116-review-lema.md`
requested changes; the rereview confirmed `RETIRED` stayed
non-satisfying.

This is a process weakness because terminal-status semantics existed, but they
were distributed across policy docs, runner code, validators, and reviewer
memory.

Missing process support:

- one canonical status-semantics module or generated status table used by
  runner and validators;
- regression tests for every terminal-status edge whenever status semantics are
  touched;
- an authority check when a task changes workflow semantics.

### 6. RnS recovered agents but did not recover stalled work

The user observed that recovery/resume did not get work moving again. TASK-119
confirmed the cause: the queue could stall behind an expired `IN_PROGRESS`
claim, with no `READY` task available, while RnS had no stale-claim owner nudge.

TASK-119 fixed this specific failure by adding stale-claim detection and a
throttled request to the task owner/claimer.

Remaining gap:

- RnS now nudges stale claims, but live hcom availability and durable
  `agents/status.json` reconciliation remain noisy. Health review
  `HEALTH-0001` treated "durable available but not live" as informational
  churn. That is acceptable for now, but it means availability truth is still
  split across live hcom state, durable status files, and watcher inference.

### 7. Review/release state could split from review artifacts

During TASK-121, the review artifact existed and showed approval, but the MAP
task state still needed an explicit `map_task.py approve` operation. Dino
applied the approval state using Lema's review record and then released the
task.

During TASK-119, both owner/reviewer activity touched the release checklist
area close together, creating an hcom collision warning and requiring the final
release artifact to be checked/corrected.

Missing process support:

- a single review command that creates the review artifact and applies the MAP
  state transition together;
- a release lock or explicit release owner handoff;
- a validator that finds "APPROVED-looking review artifact exists, but task
  state is still SUBMITTED" and routes it.

### 8. Validators duplicated a placeholder-regex bug

TASK-120 found `validate_risk_registers.py` false-positiving on the standard
HPOM comment header in `shared/RISK_REGISTER.md`. Valo also noted the same
naive placeholder-pattern class existed in another validator path.

The important failure is not that one regex was wrong. The failure is that
multiple validators implemented their own placeholder detection instead of
sharing a common helper.

Missing process support:

- a shared placeholder-detection utility;
- regression fixtures for HPOM headers and other approved template comments;
- a review checklist item for validator convention reuse.

### 9. Canonical files were referenced before they existed

`RISK_SYSTEM.md` and `PROJECT_BOOTSTRAPPING_SYSTEM.md` referenced
`MAP_System/shared/RISK_REGISTER.md`, but the actual canonical shared risk
register was not created until TASK-120's health check.

This is a scaffolding gap: documentation can declare a canonical file without a
validator confirming that the file exists.

Missing process support:

- a canonical-file existence validator for declared system files;
- a "new system creates all referenced canonical stores" acceptance criterion;
- a warning when a system references a canonical shared file that does not
  exist yet.

### 10. Emergence and retrospective loops existed late or were not drained

RETRO-0001 was useful, but it happened near the end of the cycle. Had a
mid-cycle retrospective run after TASK-107 or TASK-108, the output-path pattern
could likely have been fixed earlier.

TASK-120 also found `INS-0010` still `RAW` even though related TASK-104 was
already `RELEASED`. The content duplicated the later `IDEA-0012` process-
steward insight.

Missing process support:

- retrospective cadence triggers for long multi-task sequences;
- stale emergence checks as part of release or cycle-close;
- a formal process-steward role, or at least a rotating responsibility, for
  complex MAP-internal buildouts.

### 11. Some systems remain spec-only

The Human Interface System defines what an operator dashboard should surface,
but live CommandCenterUI wiring for MAP/hcom state remains incomplete. The
New Project Wizard has not been exercised against a real new project. Pathwell
predates the new bootstrap process and was intentionally not retrofitted.

Missing process support:

- an implementation/readiness status for each MAP system: `SPEC_ONLY`,
  `PARTIALLY_WIRED`, `LIVE`, or similar;
- a first-real-use validation requirement for wizards and bootstrap systems;
- a retrofit policy for existing projects, especially when a project predates
  a new MAP standard.

### 12. Guidelines vs MAP_System routing is correct but under-indexed

The top-level `Guidelines/` folder should remain separate because it contains
universal workspace guidance, not only MAP-specific rules. The problem is not
separation; the problem is discoverability and propagation.

During this cycle, tasks were correctly derived from
`Guidelines/MAP_repo_systems_gap_review.md`, but agents still had to remember
which universal guidance applied inside MAP and which MAP documents held the
current binding rule.

Missing process support:

- a MAP-facing routing index that points from MAP workflows to the relevant
  universal `Guidelines/` files;
- concise digests in MAP docs for rules that agents must apply during MAP work;
- a rule against duplicating full Guidelines content into MAP, to avoid two
  divergent authorities.

### 13. Event-log warnings are accepted as legacy debt

`validate_events.py` continues to pass with `errors=0 warnings=33`. The known
warnings are legacy event-shape issues: old `agent` vs `sender`, old
`timestamp` vs `created_at`, missing `artifact_paths` on old progress events,
and aliases such as `REVIEW_APPROVED` / `REVIEW_CHANGES_REQUESTED`.

These are not blocking current work, but they are persistent noise. Persistent
expected warnings reduce the signal of future warnings.

Missing process support:

- event-log normalization/backfill;
- a legacy-warning allowlist with a burn-down target;
- a validator mode that fails on new warnings while tolerating old ones.

### 14. Broadcast assignments create duplicate-owner risk

The operator's report request was broadcast to several active lab agents.
Muva and Valo initially acknowledged as if they might each produce the durable
report. Dino then claimed coordinator/owner and asked agents for findings-only
packets.

This worked, but only after an explicit coordination message.

Missing process support:

- a convention for first claimant/coordinator on broadcast tasks;
- hcom-visible ownership declaration for operator-broadcast assignments;
- a lightweight "findings packet vs main report" pattern for multi-agent
  retrospectives.

## Fixed During The Cycle

- TASK-103 mirror/output-path defects were corrected after review.
- TASK-116 fixed `RELEASED` dependency handling and preserved `RETIRED` as
  non-dependency-satisfying after review.
- TASK-118 added explicit task-authoring guidance that any edited file,
  including one-line cross-link/backlink changes, belongs in `output_paths`.
- TASK-119 added RnS stale-claim owner nudges so queue stalls behind expired
  `IN_PROGRESS` claims are no longer silent.
- TASK-120 fixed the risk-register placeholder false positive and created the
  missing `shared/RISK_REGISTER.md`.
- TASK-120 resolved stale `INS-0010` by promoting/linking it to `IDEA-0012`.
- TASK-121 created a verified MAP backup and added artifact subfolder README
  indexes without risky structural moves.

## Still Missing / Recommended Follow-Up Tasks

1. **Mirror reconciliation gate.** Add a validator that compares SQLite,
   `tasks/TASK-*.json`, and `workflow/task_graph.json` for status/owner/output
   path agreement before review and release.

2. **Diff-to-output-path validator.** Fail or warn when edited files are not in
   the task's `output_paths`. This should explicitly include shared files,
   READMEs, backlinks, templates, and indexes.

3. **Cross-link freshness validator.** Check MAP-internal links for missing
   targets and flag stale adoption wording such as future/planned/proposed
   after a system is recorded as adopted.

4. **Shared validator utilities.** Centralize placeholder detection and common
   artifact-header parsing so each validator does not invent its own regex.

5. **Review/release atomicity.** Provide a command or workflow that records the
   review artifact and state transition together, plus a release lock/handoff
   rule to prevent checklist races.

6. **Event warning cleanup.** Backfill or explicitly grandfather the 33 legacy
   warnings, then make new event warnings fail CI/review.

7. **Cycle retrospective cadence.** Require a mid-cycle retrospective after a
   threshold number of related MAP-internal tasks or after repeated review
   findings of the same class.

8. **Emergence stale gate.** Run stale emergence checks at cycle-close and
   possibly before release for tasks linked to emergence records.

9. **System implementation status.** Track whether each MAP system is spec-only
   or live-wired, and require first-real-use validation for wizards/bootstrap
   systems.

10. **Guidelines routing index.** Keep `Guidelines/` separate, but add a
    MAP-facing index that tells MAP agents which universal guidelines apply to
    which MAP workflows.

11. **Broadcast-task coordinator rule.** For hcom broadcasts, the first agent
    that claims durable ownership should declare it and request findings-only
    packets from others unless the operator asked for independent reports.

## Bottom Line

The self-update cycle did not show that MAP is broken. It showed that MAP's
process layer is ahead of its enforcement layer.

The immediate risk is not missing documentation; it is silent drift between
documentation, durable state, file mirrors, live hcom state, and reviewer
expectations. The next useful MAP improvements should reduce the amount of
correctness that lives only in agent memory.
