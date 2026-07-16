# TASK-203 Evidence: CommandCenterUI Outcome + Cost/Yield Rows

Task: TASK-203
Author: claude-lab-zero
Source: `MAP_System/inbox/helpers/ui-metrics-cards-packet.md`, TASK-182 output
boundary precedent for `/home/home/Projects/CommandCenterUI`

## Baseline commit (required first step, per the packet)

The CommandCenterUI working tree had newer uncommitted work (sidebar
sections, timers) from another session. Committed as-is, mirroring TASK-182's
`bb847f6` baseline precedent, before touching anything:

```
[master 1f8b245] Baseline: operator/agent session work, committed as baseline
 6 files changed, 2746 insertions(+), 154 deletions(-)
 create mode 100644 project-updater-status.json
```

This change's own commit lands on top of `1f8b245`, keeping the two diffs
separate.

## Design

Mirrored `/api/map/health`'s existing five-source pattern exactly (same
`ThreadPoolExecutor`, `_MAP_HEALTH_LOCK`/`_MAP_HEALTH_CACHE`, TTL, and
error-isolation semantics already used by runner/librarian/replay/rns/tokens)
rather than adding a new endpoint — the payload is small and the existing
plumbing already handles caching, force-refresh, and per-source error
isolation.

- `cost_yield_health()`: runs `python3 MAP_System/scripts/cost_yield.py
  --json` (read-only, `mode=ro` DB by construction), surfaces
  `productive_percent`, `pending_percent` + `pending_tasks`,
  `abandoned_percent` from the `spend_split` block. `status` is `warn` when
  pending spend is >=30% (currently true — the release-gate-backlog finding
  from TASK-190's operator report), else `ok`.
- `outcomes_health()`: runs `python3 MAP_System/scripts/map_metrics.py
  --json`, surfaces the `outcome_feedback` block. Zero events renders
  `"no outcomes recorded yet"` with `status: warn` (not an error) rather than
  crashing on an empty denominator.
- Both added to `_HEALTH_SOURCES`; the aggregate's `overall` status already
  takes the max severity across sources, so no aggregation logic changed.

Frontend: `MAP_HEALTH_LABELS` in `chat.js` is the single source of truth the
existing renderer (`renderMapHealth`) iterates over — adding `cost_yield:
"Yield"` and `outcomes: "Outcomes"` was the entire JS change; no new render
logic needed since the card is already fully data-driven. `chat.html`'s card
title was extended to name the two new sources. `chat.css`'s label
`min-width` was bumped 56px -> 62px so "Outcomes" doesn't crowd the text
column (cosmetic only, confirmed by the screenshot below).

No new sidebar section was added; both rows landed inside the existing MAP
runtime card body, respecting the operator's restructured sidebar layout.

## Live verification

Server started against the real MultiAgentProject MAP data on a scratch port
(8799, not the operator's live port):

```
$ COMMAND_CENTER_UI_WORKSPACE=/home/home/Projects/MultiAgentProject python3 app/server.py --port 8799
```

### Cold vs warm `/api/map/health`

```
$ time curl -s "http://127.0.0.1:8799/api/map/health?refresh=1" > /dev/null
real 0m0.864s   # cold: 7 subprocesses fan out in parallel via ThreadPoolExecutor

$ time curl -s "http://127.0.0.1:8799/api/map/health" > /dev/null
real 0m0.006s   # warm: cache hit inside the 20s TTL
```

### New sources in the JSON payload (cold run, real data)

```json
"cost_yield": {
  "status": "warn",
  "text": "55.9% shipped · 36.7% parked (58) · 1.1% abandoned",
  "productive_percent": 55.9,
  "pending_percent": 36.7,
  "pending_tasks": 58,
  "abandoned_percent": 1.1
},
"outcomes": {
  "status": "warn",
  "text": "no outcomes recorded yet",
  "outcome_event_count": 0,
  "blind_spot_count": 0,
  "blind_spot_denominator": 0
}
```

(`outcomes` correctly shows "no outcomes recorded yet" — TASK-189's outcome
feedback plumbing has zero real events logged yet, so this exercises the
zero-events path, not just the happy path.)

### Playwright DOM check

Ran against the live server root (`pwvenv` reused from an earlier session
per the packet's INS-0011 pointer):

```
Runnerroute review0 ready4 in-progress1 submitted
Librarianwikilinks resolve
Replay927 events indexed
RnSwatcher running pid 1306303 8 open incidents (8 gave-up) 6 last-live
TokensCodex 47% usedClaude non-cached 8,428,363 442,950,383 unattached observed 2 missing transcript
Yield55.9% shipped36.7% parked (58)1.1% abandoned
Outcomesno outcomes recorded yet
```

Both new rows (`Yield`, `Outcomes`) render in the DOM with the expected
labels and text, in the correct position (after `Tokens`, matching
`_HEALTH_SOURCES` insertion order).

Screenshot of the rendered card (`#map-health-card`, cropped):
`MAP_System/artifacts/reports/task203-map-health-card.png`

Server was stopped after verification; no state was left running.

## Files changed

- `/home/home/Projects/CommandCenterUI/app/server.py` — `cost_yield_health()`,
  `outcomes_health()`, both registered in `_HEALTH_SOURCES`.
- `/home/home/Projects/CommandCenterUI/src/chat.js` — two `MAP_HEALTH_LABELS`
  entries.
- `/home/home/Projects/CommandCenterUI/src/chat.css` — label column
  `min-width` 56px -> 62px.
- `/home/home/Projects/CommandCenterUI/src/chat.html` — card title text
  updated to name the two new sources.
- `MAP_System/artifacts/reports/task-203-ui-metrics-cards-evidence.md` (this
  file) and `task203-map-health-card.png`.

## Deviations from the packet

None. Extended the existing `/api/map/health` endpoint rather than adding a
new `/api/map/metrics` route (packet left this as implementer's call) because
the payload stays small and reuses proven caching/error-isolation plumbing
without a second polling loop on the client.
