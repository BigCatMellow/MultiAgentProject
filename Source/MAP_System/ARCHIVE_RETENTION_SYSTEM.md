<!-- hpom: file: ARCHIVE_RETENTION_SYSTEM.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-03 -->
<!-- hpom: verified_against: TASK-117 build, Guidelines/MAP_repo_systems_gap_review.md -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# MAP Archive / Retention System

Status: active
Decision: DEC-024
Owner: command-center
Built by: TASK-117

## What this is

`notes/brain-compaction-guide.md` already defines when to compact, what to
preserve, and what to archive. This file formalizes archive statuses and
retention rules as a standalone reference, and draws the line between
"archived" (this system) and "retired" (`CHANGE_CONTROL_SYSTEM.md`'s
artifact retirement rules) — two lifecycle stages that look similar but
answer different questions.

## Core principle

```
Do not delete useful history, but do not let old history pretend to be current truth.
```

## Archive vs. retirement: the distinction

| | Retirement (`CHANGE_CONTROL_SYSTEM.md`) | Archiving (this system) |
|---|---|---|
| Question answered | Is this specific artifact still valid? | Is this content still active working memory? |
| Where it stays | In place, marked `superseded`/`RETIRED`/`DISMISSED` | Moved to `archive/`, summarized forward |
| Trigger | A decision was superseded, a task was duplicated/cancelled, an idea was dismissed | Active memory grew past its budget, or content is old enough to no longer inform current work |
| Content survives as | The original artifact, unmodified, with a status field | A compaction summary, with the raw material still retrievable |

A single file can go through both: a decision gets superseded in place
(retirement) long before the file it lived in is ever compacted
(archiving).

## Archive statuses

| Status | Meaning |
|---|---|
| `ACTIVE` | current working memory; read by default per `CONTEXT_SYSTEM.md` |
| `COMPACTED` | content has been summarized forward; the summary is active, the raw file moved to `archive/` |
| `HISTORICAL` | already in `archive/`, kept for provenance, not expected to inform current decisions |

## Retention rules

- Nothing in `archive/` is ever deleted outright — per
  `brain-compaction-guide.md`'s Safety Rules, raw history is preserved,
  only active-memory copies are compacted.
- A compaction summary must name its source paths (already required by
  `brain-compaction-guide.md`'s Compaction Summary Shape and reaffirmed by
  `CONTEXT_SYSTEM.md`'s compression rules) so the archived original is
  always reachable from the summary.
- `HISTORICAL` content does not get restored to `ACTIVE` status casually —
  if a task genuinely needs it, that need itself should be logged (a
  Research Brief citing it, a repair record referencing it) rather than
  silently promoting archived content back to canonical status.

## Compaction cadence

Unchanged from `brain-compaction-guide.md`'s existing Compaction Triggers
section — this system does not introduce a new cadence, it names the
existing one as this system's cadence for consistency:
run compaction when active memory exceeds its stated budget or when a
project phase closes, whichever comes first.

## Marking stale artifacts

- A file whose HPOM `last_verified` date is far behind current work, or
  whose content contradicts `shared/current-state.md`, is a `DRIFT`-class
  finding per `SELF_REPAIR_SYSTEM.md` before it is an archiving question —
  fix or update it first; archive only once it is genuinely done being
  active memory, not as a way to avoid updating it.
- Do not archive a file merely because no one has read it recently — the
  compaction trigger is active-memory budget or phase closure, not read
  frequency.

## Relationship to other systems

```
Self-Repair flags stale-but-still-active content as drift, not archive fodder.
Change Control's retirement rules mark an artifact invalid in place.
Archive/Retention moves genuinely inactive content out of the active-memory budget.
Context System governs what counts as forbidden/historical context by default.
```

- **`SELF_REPAIR_SYSTEM.md`**: a file that is stale *and still being read
  as if current* is a repair target, not an archiving target — archive
  only after the content is confirmed no longer load-bearing.
- **`CHANGE_CONTROL_SYSTEM.md`**: retirement (marking superseded/RETIRED/
  DISMISSED in place) is a separate lifecycle step from archiving (moving
  to `archive/`); a retired artifact may stay `ACTIVE`-status for a long
  time if it is still informative context (e.g., a superseded decision
  that explains why the current one exists).
- **`CONTEXT_SYSTEM.md`**: that system's Forbidden Context Loading and
  Stale Context Handling sections already say not to load `archive/` by
  default and to treat old snapshots as orientation-only; this system is
  where the archiving decision behind that default is made.

## Related files

- `notes/brain-compaction-guide.md` [[brain-compaction-guide]] — the compaction mechanics this system
  formalizes statuses and retention rules around
- `CHANGE_CONTROL_SYSTEM.md` [[CHANGE_CONTROL_SYSTEM]] — where artifact retirement (a different
  lifecycle stage) is defined
- `SELF_REPAIR_SYSTEM.md` [[SELF_REPAIR_SYSTEM]] — where stale-but-active content is a repair
  target, not an archiving target
- `CONTEXT_SYSTEM.md` [[CONTEXT_SYSTEM]] — where archive/historical content is excluded from
  default context
- `Guidelines/MAP_repo_systems_gap_review.md` — the gap review that
  identified this system as a secondary gap
