<!-- hpom: file: artifacts/command-center-ui/task-182-map-health-cards.md -->
<!-- hpom: project: MAP -->
<!-- hpom: state_owner: command-center -->
<!-- hpom: status: CURRENT -->
<!-- hpom: last_verified: 2026-07-14 -->
<!-- hpom: verified_against: TASK-182 live endpoint + DOM check -->
<!-- hpom: confidence: HIGH -->
<!-- hpom: supersedes: NONE -->
<!-- hpom: superseded_by: NONE -->

# TASK-182: CommandCenterUI MAP Runtime Health Cards

- task: TASK-182
- owner: claude-lab-mira
- date: 2026-07-14
- status: implemented + live-verified
- external repo: `/home/home/Projects/CommandCenterUI` (operator-approved output
  boundary: hcom #33409 lead assignment + "get it done and implemented as
  needed" directive, closing the gap TASK-175 deferred)

## What was built

- ep: `GET /api/map/health` in `app/server.py` — read-only aggregate of 4 MAP
  runtime sources, each with per-source error isolation:
  - runner: `graph/runner.py` via MAP venv python → route, ready/in-progress/
    submitted/blocked counts, halt state (warn on halt or blocked tasks)
  - librarian: `scripts/librarian.py validate` → finding_count (warn if >0;
    validator's findings-exit-1 is treated as parseable output, not failure)
  - replay: `scripts/session_replay.py status` → safe_for_mission_control,
    drift findings, indexed rows (status subcommand only — never `build`)
  - rns: `agents/limit-watcher-state.json` read directly → open/gave-up
    incident counts, last-live roster (warn when open incidents exist)
- cache: 20s TTL behind a lock (UI polls at 30s; lock also serializes
  cold-cache fetches so concurrent requests can't stampede MAP scripts);
  sources fetched in parallel (ThreadPoolExecutor) so cold latency ≈ max,
  not sum
- ui: "MAP runtime" sidebar card in `chat.html`/`chat.js`/`chat.css` — header
  dot = worst source status, one dot+label+terse-text row per source,
  offline-degrade row if the endpoint itself is unreachable
- docs: README section documenting the card, endpoint, sources, and the
  read-only guarantee

## Read-only guarantee

No MAP_System writes from the UI path: route computation, `validate`, and
`status` subcommands only. The one watcher source is a plain file read.
`session_replay.py build` (which writes the derived index) is deliberately
not called.

## Live verification (2026-07-14)

- `node --check` chat.js: pass; `py_compile` server.py: pass
- server started on :8799; cold `GET /api/map/health`: 0.74s, warm: 0.02s
- endpoint returned overall=warn with all 4 sources populated:
  runner ok (`route wait_or_reconcile · 0 ready · 2 in-progress`),
  librarian ok (`wikilinks resolve`), replay ok (`927 events indexed`),
  rns warn (`10 open incidents (8 gave-up) · 2 last-live`) — the warn is
  honest live state (stale watcher incidents), exactly what the card exists
  to surface
- Playwright DOM check (chromium, against the running server): 4 rows render
  with correct labels/dots/text, header dot=warn; screenshot captured;
  script asserts label order, dot values, and non-empty text — PASS
- the DOM check even caught live state change mid-run: route flipped to
  `review · 1 submitted` when TASK-183 was submitted during the test

## Testing note (found during implementation)

First live call caught two integration bugs that static review missed:
`session_replay.py` invoked with a cwd-relative path that didn't resolve, and
`librarian.py validate`'s exit-1-on-findings being misread as script failure.
Both fixed and re-verified live. Reinforces [[INS-0016-validator-coverage-must-include-live-command-surfaces-not-only-d|INS-0016]]:
exercise the live command surface, not just the code.

## Git

- baseline commit `bb847f6` (pre-existing uncommitted ProjectUpdater card work,
  committed separately so this task's diff is reviewable in isolation)
- TASK-182 commit follows in the same repo; local only, no push (push needs
  explicit operator go-ahead per established norms)

## Follow-ups (not in this task)

- RnS warn will stay amber until stale watcher incidents are pruned/reset
  (TASK-176's lane; card makes the state visible rather than fixing it)
- Old `/app.html` dashboard untouched; if the operator wants the same cards
  there, that is a small follow-on
