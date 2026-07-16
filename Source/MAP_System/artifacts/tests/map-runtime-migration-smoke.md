# MAP Runtime Migration Smoke Check (TASK-148)

Task: TASK-148
Tester: claude-lab-zera
Date: 2026-07-13
Companion: `MAP_System/artifacts/planning/map-runtime-migration-plan.md`

Purpose: pre/post validation commands for each state surface named in the
migration inventory, to run before and after any MAP 6.13 wave lands, so
drift is caught the same session it's introduced rather than reconstructed
later.

## Canonical Path

```bash
cat MAP_System/shared/canonical-repo.md | grep -A2 "Canonical Local Repo"
pwd  # must resolve under /home/home/Projects/MultiAgentProject
git remote get-url origin
git branch --show-current
```

Expected pre/post: canonical path, remote, and branch (`main`) unchanged
across a wave. If any of these differ post-change, stop — a wave should
never move canonical repo state.

## Task Mirrors (SQLite / task JSON / task graph)

```bash
python3 MAP_System/scripts/validate_task_mirrors.py
```

Expected pre: `Task mirror validation passed.`
Expected post: `Task mirror validation passed.` — run again after any wave
that adds/changes task fields, status, or claims. A failure here means the
wave edited one mirror (SQLite, `tasks/TASK-*.json`, or `task_graph.json`)
without the other two.

## Event Log Baseline

```bash
python3 MAP_System/scripts/validate_events.py --fail-on-new
```

Expected pre and post: exits clean against `events/warning_baseline.json`
(33 accepted legacy warnings as of this task). A wave that adds new required
event fields should not cause this to newly fail — new fields must be
optional until a separate, explicit step makes them required.

## Agent Identity Consistency

```bash
python3 -c "
import json, sqlite3
status = json.load(open('MAP_System/agents/status.json'))['agents']
conn = sqlite3.connect('MAP_System/map.db')
db_agents = {r[0] for r in conn.execute('SELECT agent_id FROM agents')}
status_agents = set(status)
print('in map.db not status.json:', sorted(db_agents - status_agents))
print('in status.json not map.db:', sorted(status_agents - db_agents))
"
```

Expected pre (as of this task, 2026-07-13): a non-empty first list is
EXPECTED until Step 0 of the rollout plan (reconciliation fix) lands — this
is documented, known drift, not a regression. Expected post-Step-0: both
lists shrink toward empty for any agent that should be tracked; retired/
service identities (`map-task`, `reconcile`, `langgraph-runner`,
`limit-watcher`) are an accepted permanent exception and should be
enumerated explicitly once Step 0 ships, not silently ignored.

Regression check for any wave after Step 0: this script's first list must
stay empty — a new agent session claiming a task should never hit the FK
failure this task hit when registering `claude-lab-zera`.

## Full Repo Test Suite

```bash
bash MAP_System/scripts/run_tests.sh
```

Expected pre and post: all checks pass (37 checks as of TASK-143's baseline;
count will grow as new waves add their own focused tests — compare the
printed count, not just exit code, to catch a wave that silently skipped
registering its own test).

## Shared-State Metadata Gate

```bash
python3 MAP_System/scripts/validate_shared_state.py
```

Expected pre and post: 0 stale files. Any wave that updates
`shared/current-state.md`, `shared/decisions.md`, or
`shared/improvement-backlog.md` must refresh the HPOM header fields in the
same change or this gate fails.

## CommandCenterUI Boundary Check (manual, no automated command available in this repo)

- Confirm no MAP_System change assumes a file inside
  `/home/home/Projects/CommandCenterUI` was edited in the same commit —
  that repo is out of this repo's test/validation scope. If a wave's
  acceptance criteria reference CommandCenterUI behavior, the smoke check
  is: a separate task/handoff exists for the CommandCenterUI-side change,
  named explicitly (see `map-runtime-migration-plan.md`, "CommandCenterUI
  Coordination").

## Rollback Smoke Check

For any wave that adds a lock file under `.locks/` or a new table/column:

```bash
ls MAP_System/.locks/
sqlite3 MAP_System/map.db ".schema" | grep -c "CREATE TABLE"
```

Record the pre-change count of lock files and tables. Post-change, confirm
the new lock file or table exists, and that removing it (in a disposable
copy, never canonical `map.db`) does not orphan any task in `IN_PROGRESS`
with a lease that never expires.

## Chaos/Fault-Injection Safety Check

Before running any Wave 7 chaos test:

```bash
test -f MAP_System/map.db && cp MAP_System/map.db /tmp/map-chaos-test-copy.db
```

Do not run fault-injection (kill mid-task, malformed event, simulated
poisoned state) against the file at `MAP_System/map.db` or
`MAP_System/events/events.jsonl` directly. Run it against the copy, or a
dedicated fixture DB, per the existing pattern in
`artifacts/tests/reconcile-test.md` (temporary replacement DB, restored
after the fixture run).
