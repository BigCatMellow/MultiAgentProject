# TASK-129 MAP System Adherence Audit — Final Report

Task: TASK-129
Coordinator (Process Steward, PROMO-0007/IDEA-0012): claude-lab-valo
Contributors: codex-lab-dino (TASK-131, cross-link checker), codex-lab-muva
(TASK-130, real-usage evidence), codex-lab-lema (independent review of both)
Date: 2026-07-03
Trigger: operator concern, hcom #22305 — "I worry that we have blown
through all the new systems... not enough of making sure the system in
place is used and implemented properly."

## Verdict

The concern was valid, and this audit found concrete evidence of it — not
just the possibility of it. Three real, fixable defects were found and
corrected during the audit itself. The systems are now genuinely more
"one base" than before this audit ran, but several remain
documented-and-validated without being exercised in practice.

## What this audit did differently from the build sequence

Rather than one agent asserting completeness from memory, this audit:

1. Used `graph/runner.py`'s live state as the literal starting point
   (queue idle, all agents available) before any work began.
2. Split into three independently-owned, independently-reviewed MAP
   tasks (TASK-129 coordination, TASK-130 usage evidence, TASK-131
   cross-link verification) rather than one agent doing everything.
3. Required every finding to be verified against the filesystem, not
   recalled from the session's own memory of what was built.
4. Caught and self-corrected process failures live: two duplicate
   coordinator tasks (TASK-127/128) were created independently by other
   agents reacting to the same operator message and retired themselves
   without operator intervention; a stale-report race was caught by
   lema's independent re-run and resolved by dino regenerating; a
   release-checklist metadata collision (released_by mismatch) was
   caught and fixed by lema/dino themselves.

## Finding 1: Cross-links were not actually bidirectional (fixed)

A manual grep spot-check (mine) found 3 one-way gaps. A rigorous
purpose-built checker (dino, TASK-131, `scripts/check_system_crosslinks.py`,
parsing only `## Related files` sections) found 7 more that the manual
grep missed or mis-attributed — including correctly identifying that one
of my "fixes" had matched an incidental body-text mention rather than a
real cross-link.

- **Before this audit**: 8 systems already existed, most with `Related
  files` sections written as they were built, but never checked against
  each other as a whole.
- **After this audit**: 60 directed links across 11 systems, 30 fully
  bidirectional pairs, 0 one-directional gaps. Verified independently by
  dino (builder), lema (reviewer), and re-confirmed by me.

This directly validates the operator's "just different blocks, not one
base" concern — cross-linking was aspirational in each system's own
"Relationship to other systems" section, but not actually complete until
checked mechanically.

Record: `MAP_System/artifacts/audits/system-crosslink-bidirectionality-2026-07-03.md`

## Finding 2: A real ID collision existed in the Self-Repair System (fixed)

Two unrelated repair records both claimed `REPAIR-0001` — one from
TASK-116 (dino), one from TASK-120 (valo) — because `repairs/` has no
atomic ID allocation, unlike `map_task.py create --task-id auto` and
`map_emergence.py`. This is exactly the failure class those two tools
exist to prevent, applied to a third system that never got the same
treatment.

Fixed: renamed the later record to `REPAIR-0003`, updated its live
cross-references, and logged the root-cause fix (`map_repair.py` ID
allocation) to `shared/improvement-backlog.md` as a proposal, not built
unilaterally.

Record: `MAP_System/repairs/REPAIR-0004-repair-record-id-collision.md`

## Finding 3: Real usage is genuinely uneven across the 11 systems

Per TASK-130 (muva, independently confirmed by lema):

| System | Real usage | Evidence |
|---|---|---|
| Self-Repair | Genuinely used | 4 repair records, 1 health check, drove TASK-116/120/129 fixes |
| Risk | Genuinely used | 2 real risk registers (MAP-system + ProjectUpdater), validator in `run_tests.sh` |
| Change Control | Genuinely used, mechanically enforced | Every recent release goes through `release_task.py`'s gate |
| Emergence (DEC-026) | Genuinely used, mechanically enforced | ProjectUpdater backfilled + release gate blocks without consideration |
| Project Bootstrapping | Used once | ProjectUpdater is the only project bootstrapped under it so far |
| Decision/Authority | Used during adoption only | `Class:` tag used in DEC-018 through DEC-026; no post-adoption decision yet to prove the habit continues |
| Research | Documented and validator-backed, not exercised | No real Research Brief/Source Map/Summary artifact exists yet — every project so far explicitly had no external-fact dependency |
| Context | Documented and validator-backed, not exercised | Zero real context packets built; a validator (TASK-109) exists but nothing has used the packet format itself |
| Security/Permissions | Partially used as convention | "Security Second Pass" appears in multiple reviews; no structured security artifact or validator |
| Human Interface | Specification only | No live dashboard implementation consumes the content contract yet (this was already known/open per `shared/improvement-backlog.md`) |
| Archive/Retention | Specification only | Concepts referenced in retirement/RETIRED handling; no standalone archive/retention action taken yet |
| Retrospective | Used once, weak storage | Only RETRO-0001 exists, embedded in the system doc rather than a standalone record; no successor despite a full new phase happening since |

Record: `MAP_System/artifacts/audits/task-130-map-systems-real-usage-evidence.md`

## Synthesis: why some systems get used and others don't

The systems that are genuinely and repeatedly used (Self-Repair, Risk,
Change Control, Emergence) share one trait: something makes using them
the path of least resistance or mechanically required. Change Control
and Emergence are hard-gated by `release_task.py`. Self-Repair and Risk
got used because this very audit needed them.

The systems that are specification-only (Human Interface, Archive/
Retention, Context, Research) share the opposite trait: using them
requires an agent to proactively remember to do something extra with no
gate checking that they did. This is the same root cause DEC-026 already
fixed for Emergence — the fix generalizes.

## Recommendation (not built here — proposing for a separate task)

Per muva's TASK-130 routing suggestions, several of these are legitimate
follow-ups, but building all of them now would repeat the exact mistake
this audit is checking for (moving fast without verifying). Recommend:

1. **Do not** force Context Packets or Research Briefs into existence
   where the honest answer is "not needed yet" (per Research's own
   evidence — ProjectUpdater correctly had no external-fact dependency).
   Revisit when a task genuinely needs one.
2. **Do** consider a lighter-weight version of the Emergence-style gate
   for Retrospective cadence specifically, since RETRO-0001 already
   proved its value (caught and fixed a real recurring pattern) and a
   full new phase has passed without a successor.
3. **Do** build the `map_repair.py` ID-allocation fix (Finding 2) since
   it's small, mechanical, and prevents a concrete recurring failure
   mode, not a speculative one.
4. Human Interface's live dashboard wiring remains a known, already-
   tracked open item (`shared/improvement-backlog.md`) — this audit adds
   no new urgency to it beyond confirming it's still open.

## On "one agent at the head, directing and delegating" (operator's core ask)

This audit itself is offered as the answer, not just a report about one:
`PROMO-0007`/`IDEA-0012` (previously captured, never acted on until this
exact concern was raised twice) proposed a bounded Process-Adherence
Steward role rather than a new permanent agent identity. This cycle used
it: one agent (me) held the role, used `graph/runner.py` as the literal
input for what to route next, delegated two independent bounded
mechanical slices to Codex agents, and routed every finding through
normal task-review-release rather than fixing things solo. Recommend
this become the standard opening move for any future multi-system or
multi-task initiative, invoked explicitly (any core agent may hold it for
one cycle), rather than assumed implicitly the way this session's
11-system build proceeded without one.

## Verification

```text
check_system_crosslinks.py (TASK-131): 60 directed links, 30 bidirectional, 0 gaps
map_emergence.py validate: OK, 35 artifacts checked
map_emergence.py stale: no findings
validate_task_graph.py: PASS
validate_shared_state.py: 19 checked, 0 failures
validate_decisions.py: 26 decisions checked, 0 failures
full MAP suite (scripts/run_tests.sh): pass=33 fail=0 total=33
```

## Related records

- `MAP_System/artifacts/audits/system-crosslink-bidirectionality-2026-07-03.md` (TASK-131)
- `MAP_System/artifacts/audits/task-130-map-systems-real-usage-evidence.md` (TASK-130)
- `MAP_System/repairs/REPAIR-0002-one-way-cross-link-gaps-between-11-systems.md`
- `MAP_System/repairs/REPAIR-0004-repair-record-id-collision.md`
- `MAP_System/emergence/promotions/PROMO-0007-idea-0012.md`
- `MAP_System/shared/improvement-backlog.md` (map_repair.py ID allocation, Retrospective cadence)
