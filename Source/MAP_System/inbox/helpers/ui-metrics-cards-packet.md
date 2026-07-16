# Work Packet: CommandCenterUI Outcome + Cost/Yield Cards

Intended implementer: claude-lab-zero
Dispatcher: claude-lab-mira (lead)
Source: TASK-182 follow-on (operator-approved output boundary precedent for
`/home/home/Projects/CommandCenterUI`); consumes today's new data sources
(TASK-189 outcome metrics, TASK-190 cost_yield.py). Operator-visible value:
the two findings they care about (37% spend parked at release gate;
validator blind-spot series) become glanceable instead of buried in reports.

## Design (mirror TASK-182's proven pattern exactly)

1. `app/server.py`: extend the existing `/api/map/health` aggregate (or add
   `/api/map/metrics` if payload size argues for it — your call, justify) with
   two read-only sources behind the SAME cache/lock/error-isolation plumbing:
   - `cost_yield`: run `python3 MAP_System/scripts/cost_yield.py --json`
     (read-only by construction, mode=ro DB), surface: productive %,
     pending-at-release-gate % + task count, abandoned %.
   - `outcomes`: `python3 MAP_System/scripts/map_metrics.py --json` outcome
     block, surface: outcome_event_count, blind_spot_rate (n/denominator).
     Zero events → show "no outcomes recorded yet", not an error.
2. `src/chat.js/css/html`: two compact rows in the existing "MAP runtime"
   card (do NOT add a new sidebar section — the operator restructured the
   sidebar; respect the current layout and only touch the MAP runtime card
   body). Yield row example: "54% shipped · 37% parked (53) · <1% abandoned".
   Outcomes row: "no outcomes yet" or "N outcomes · blind-spot x/y".
3. IMPORTANT repo state: the CommandCenterUI working tree has newer
   uncommitted work (sidebar sections, timers) by someone else. Baseline-
   commit it FIRST as its own commit (same as TASK-182's bb847f6 precedent,
   message crediting "operator/agent session work, committed as baseline"),
   then your changes as a second commit. Do not mix the diffs.
4. Verify live: server up, curl cold+warm, Playwright DOM check for the two
   new rows (pwvenv exists in the session scratchpad or rebuild per INS-0011),
   record evidence in a MAP-side artifact.

## Task record

--task-id auto (announce), output paths: the four UI-repo files + MAP-side
evidence artifact. Cite this packet + TASK-182 boundary precedent in the
description. claim_review() for your reviewer when submitting.
