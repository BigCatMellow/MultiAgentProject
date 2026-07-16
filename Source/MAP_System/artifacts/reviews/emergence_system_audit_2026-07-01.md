# Emergence/Insight System Audit — 2026-07-01

Owner: claude-lab-rose
Scope: root `MAP_System/emergence/`, Pathwell's project-local emergence
folders, and CommandCenterUI/DarkMellow (checked for any local emergence use).
Part of the operator-requested full MAP-system audit (hcom #14289), folded
into codex-lab-limo's consolidated audit artifact.

## Summary

The emergence system works when someone deliberately closes the loop, and it
was built and validated correctly (`map_emergence.py validate`/`rebuild-index`
both function). But most records in the root registry never get closed —
they're either hollow test stubs that were never filled in, or real insights
whose underlying work finished without anyone going back to update the
tracking record. Only one full pipeline (insight → idea → promotion → real
artifact) has ever completed end-to-end, and it happened today, in Pathwell,
not at the root level.

## Finding 1 — 4 of 12 root insight/idea records are empty test stubs

`INS-0002`, `INS-0003`, `IDEA-0002`, `IDEA-0003` all contain the literal
placeholder content `text` in every free-text field, with every checkbox
unchecked. These read as smoke-test artifacts from building the emergence CLI
itself (`IDEA-0002`'s "Why now" field literally says "The Command Center Lab
is actively testing emergence workflow"), never cleaned up or removed after
serving that purpose. `map_emergence.py validate` passes them anyway —
schema/structure validation, not content validation — so they sit in the
"active" index indefinitely alongside real records with no way to
distinguish one from the other at a glance.

**Recommendation:** either fill these in retroactively (unlikely to be worth
it, they're test artifacts) or mark them `DISMISSED`/remove them so the index
reflects only real capture.

## Finding 2 — the emergence CLI's own tracking records were never closed

`INS-0001`, `IDEA-0001`, and `PROMO-0001` (root) all concern building the
emergence CLI itself. The underlying task, `TASK-052`, is `RELEASED` — the
CLI is the exact tool used throughout this session (`map_emergence.py`,
running cleanly). But the tracking records are still `RAW` / `CANDIDATE` /
`PROPOSED`, and `PROMO-0001`'s Approval field literally reads `TBD` / `TBD`.

This is the same pattern found and fixed in Pathwell's own emergence records
earlier today (`INS-0001` there was left `RAW` and `IDEA-0001` stuck at
`CANDIDATE` despite the debt-payment pass being fully executed). It appears
twice, independently, in two different parts of the same system — evidence
this is a systemic gap, not a one-off oversight: **nothing in the current
process closes an emergence record when its underlying work finishes.**

## Finding 3 — two promotion records are incomplete templates

`PROMO-0002` and `PROMO-0003` both still contain the literal placeholder
`IDEA-####` as their source idea reference — a dangling, unresolvable link —
and both have every checkbox unchecked and `Required next action: -` (blank).
Neither was ever finished being written, let alone approved.

## Finding 4 — Synthesis and Experiment categories have never been used

Zero `SYN-*` or `EXP-*` records exist anywhere in the root system, and (per
earlier findings this session) zero in Pathwell's local folders either. The
emergence system has four intended capture types; only two (Insight, Idea)
have ever actually been used, system-wide, since the CLI was built.

## Finding 5 — the one clean full pipeline happened today, in Pathwell

Pathwell's `INS-0001` → `IDEA-0001` → `PROMO-0001` → `Story_Files/debt_payment_checklist.md`
(all today, TASK-020/021) is the only example anywhere in the system of an
emergence capture actually completing its full lifecycle: captured, reviewed,
promoted, and turned into a durable, reusable artifact with its status
correctly reflecting that. It required the operator directly asking whether
emergence had produced anything new — twice — before it happened. Left to
its own momentum, this pass would also have stalled at "captured, never
closed," matching every other record in the system.

## Root cause (proposed)

Emergence capture is treated as a one-way action — write the record, move
on — rather than a lifecycle with an expected close-out step. Nothing
prompts an agent to revisit a record once its related task finishes.
`db/claims.py` enforces this discipline for task claims (lease, heartbeat,
submit); nothing equivalent exists for emergence records.

## Recommendation

Add "check for related open emergence records" as a step in task closure
(`submit_task`/`RELEASED` flow), the same way task closure already checks
task-graph validity. Smallest safe version: a script that cross-references
emergence records' `Related task` field against task status and flags
records whose task is `RELEASED`/`APPROVED` but whose own status is still
`RAW`/`CANDIDATE`/`PROPOSED` — surfacing exactly Finding 2's pattern
automatically instead of relying on an operator to ask.
