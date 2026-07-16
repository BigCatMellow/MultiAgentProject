# Retrospective Record

Retrospective ID: RETRO-0002
Cycle covered: TASK-135 through TASK-139 (ProjectUpdater/CommandCenterUI integration: status export, sidebar card, Areas-sidebar removal, review-conflict routing fix, runtime bugfix)
Run by: claude-lab-vino
Date: 2026-07-04

See `MAP_System/RETROSPECTIVE_SYSTEM.md` for the reasoning behind this
loop and its relationship to Self-Repair (incident scale) vs. this system
(cycle scale). This is the first standalone retrospective record filed
under this system — RETRO-0001 exists only as a worked example embedded
in `RETROSPECTIVE_SYSTEM.md` itself, which TASK-129's audit already flagged
as weak storage.

## What worked

- Independent review held even under time pressure: TASK-135, TASK-136,
  TASK-138, and TASK-139 were all independently reviewed (not
  self-approved) with live verification (curl against a running server,
  Playwright, re-run validators) rather than trusting the submitter's own
  claims. Two of these (TASK-135, TASK-139) were network-facing/write-
  capable changes and got an explicit security pass per IDEA-0004's
  convention (CSRF/same-origin check, command-injection check, GET-vs-POST
  trigger surface).
- The no-self-review rule actually caught something real: on TASK-137
  (Areas-sidebar removal), I recognized I couldn't review it because I'd
  authored the actual code change in the same shared file, and declined
  rather than rubber-stamping my own work.
- Root-cause diagnosis before acting: the "ProjectUpdater card says
  offline" bug report was traced to a specific, verifiable cause (a
  long-running server process predating the code that added the new
  endpoint) before any fix was attempted, rather than guessing.

## What failed / caused rework

- TASK-137's self-review conflict was initially escalated to the operator
  as a request instead of using the already-existing visible-helper path
  (`AGENTS.md`'s helper policy, `helper-agent-guide.md`). The operator
  called this out directly. Fixed same-cycle as TASK-138 (see table
  below) and the very next conflict (also TASK-137, after the operator's
  correction) was actually routed to a visible helper (`bula`,
  `MAP_System/inbox/helpers/helper-review-task-137.md`,
  `artifacts/reviews/task137-review-bula.md`) — proof the fix was
  exercised immediately, not just documented.
- A destructive/impactful action (restarting a long-running server
  process I did not start) was correctly blocked by the sandbox's auto
  classifier on first attempt, requiring an explicit operator go-ahead
  before it could proceed. Not a process failure — the guardrail worked
  as intended — but worth naming as the moment friction was highest in
  this cycle.
- INS-0015 was initially filed as unfilled template boilerplate (no real
  Trigger/Evidence/Risk/Scope content, no next-action box checked) despite
  documenting a real, just-happened incident. Caught in TASK-138's review
  as a non-blocking finding and fixed in a same-day follow-up.

## What agents misunderstood

- That "routine no-self-review reviewer conflict" and "needs an operator
  decision" are different categories. The helper-routing policy existed
  in spirit (helper-agent-guide.md already described helpers generally)
  but had no explicit statement that this specific, common conflict type
  should default to a helper rather than an operator ask. TASK-138 closed
  that gap.

## What rules were unclear

- Nothing new surfaced beyond what TASK-129's audit already found about
  output-path registration; no cross-linking or output-path disputes
  occurred in this cycle.

## What should become permanent

| Pattern | Proposed fix | Type | Status |
|---|---|---|---|
| Routine no-self-review conflicts got escalated to the operator instead of using the existing helper path | Explicit "Routine Reviewer Conflict Routing" section in `AGENTS.md` + "Review-Conflict Default" in `helper-agent-guide.md` | decision + template/doc change | APPLIED (TASK-138) |
| Emergence insight records get filed as unfilled boilerplate even when they document a real incident | No new validator proposed here — `map_emergence.py validate` already checks placeholder resolution structurally; the gap was an authoring habit, not a missing check. Recommend reviewers keep flagging boilerplate content as a non-blocking finding (as done in TASK-138's review) rather than adding a mechanical gate that would just check box-ticking, not substance | convention (reviewer discipline) | PROPOSED |
| `map_emergence.py`'s `next_id()` had no lock at all — a latent version of the exact REPAIR-0001 collision class, discovered while doing this cycle's systems-adherence pass, not something this cycle's tasks triggered directly | Per-kind file lock (`fcntl.flock`) around ID allocation + existence-check + write in `create_artifact()`, reproduced the collision before the fix and confirmed it closes after | validator/code fix | APPLIED (TASK-141, filed in this same retrospective's parent task) |

## Follow-up

- [x] Logged in `shared/improvement-backlog.md` if not immediately actioned — see the two still-open items below
- [x] Captured as an `INS-NNNN` insight if genuinely novel — INS-0015 (TASK-137 routing) already captured; the `map_emergence.py` lock gap is being logged as a repair record instead, since it's a mechanical fix rather than a process-judgment insight
- [ ] Routed through `CHANGE_CONTROL_SYSTEM.md` if a fix is approved and ready to apply — the `map_emergence.py` lock fix goes through the normal task-review-release gate like any other change (TASK-141)

## Notes

- Two recommendations from the prior TASK-129 audit remain open and are
  not addressed by this cycle: `map_repair.py`'s ID-allocation helper
  (`repairs/` still has no atomic allocation) and this retrospective
  cadence itself only just got its first standalone record. Both are
  small enough to be worth a follow-up task rather than folding into this
  one, per the same "don't build everything at once" discipline the prior
  audit recommended.
- This cycle also produced a live-verified security-review habit
  (explicit CSRF/injection checks on TASK-135 and TASK-139) that wasn't
  forced by any gate — worth watching whether it holds up without one, or
  whether it should become IDEA-0004's mechanical second-pass requirement
  applied more broadly.
