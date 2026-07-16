# MAP Session Replay Read Model Design

Task: TASK-172
Owner: codex-lab-mozu
Status: draft for review
Created: 2026-07-14
Depends-On: TASK-171

## Purpose

Design a MAP-native session replay/read model for mission-control and the
Command Center. The model should make task, trace, agent, hcom, and event
history easy to inspect from one surface without changing source authority or
copying external observability code.

TASK-171 identified `repo/agents-observe-main` as the strongest immediate
pattern: local event capture, indexed replay, filters, and transcript views.
MAP should borrow the architecture shape, not the Node service, Docker stack,
or storage implementation.

## Current Baseline

Existing MAP surfaces already support pieces of replay:

- `MAP_System/events/events.jsonl`: append-only MAP lifecycle events.
- `MAP_System/map.db`: canonical task claim/dispatch database.
- `MAP_System/tasks/TASK-NNN.json`: human-readable task mirrors.
- `MAP_System/workflow/task_graph.json`: human-readable queue mirror.
- `MAP_System/scripts/event_trace.py`: new task trace convention
  (`trace_id=task:TASK-NNN`) plus optional actor/action/target fields.
- `MAP_System/scripts/mission_control_tui.py`: read-only dashboard,
  task/agent/attention/event drilldowns, source-drift checks.
- `hcom events --name mozu`: local hcom event stream with message, status,
  lifecycle, command, file, intent, thread, reply-to, and mention filters.
- `hcom transcript --name mozu`: hcom-tracked conversation transcript access.

The gap is that these are read live and separately. Mission-control can show
recent events, but it cannot yet answer "show the complete replay for this
task/agent/session/trace, including related hcom messages and transcript
pointers" without an agent manually joining logs.

## Source Authority

The replay model must be derived. It must not become a new writer or a second
source of truth.

| Data | Authority | Replay Use |
|---|---|---|
| Task lifecycle and trace events | `MAP_System/events/events.jsonl` | Primary ordered MAP event stream. |
| Task status, owner, attempts, leases | `MAP_System/map.db` | Current task state and claim metadata. |
| Human-readable task records | `MAP_System/tasks/*.json` | Output paths, criteria, dependency context, mirror drift checks. |
| Queue and route state | `MAP_System/graph/runner.py --pretty` | Current route and queue membership; not historical replay by itself. |
| Hcom live/status/message events | `hcom events` CLI | External communication/status evidence, imported by event ID. |
| Hcom transcripts | `hcom transcript` CLI | Optional pointer targets for deeper context; do not inline full transcripts by default. |
| Agent liveness | `MAP_System/shared/liveness-state.md` | Current state overlay, not historical authority. |
| Review records | `MAP_System/artifacts/reviews/*.md` | Evidence for approval/change decisions via task output paths and events. |

Raw hcom storage currently exists under `/home/home/.hcom/hcom.db`, but the
design should treat the `hcom` CLI as the stable interface. Direct DB reads
should be a later optimization only if hcom exposes a documented stable schema
or MAP owns a compatibility adapter with tests.

## Derived Store

Recommended local derived store:

```text
MAP_System/runtime/session_replay.sqlite
```

`runtime/` does not exist today, so the implementation task should either
create it with a README explaining "derived, rebuildable, safe to delete", or
choose an existing derived-state folder if MAP establishes one first.

The store is disposable:

- It can be rebuilt from canonical sources.
- It is never edited by agents or the TUI except through a replay-index build
  command.
- It should not be committed unless MAP later decides to version fixtures.
- It must carry source offsets/checksums so drift is visible.

Suggested tables:

| Table | Purpose |
|---|---|
| `source_snapshots` | One row per indexed source with path/command, size, mtime or high-water mark, checksum when available, and indexed_at. |
| `replay_events` | Normalized event rows: source, source_event_id, created_at, kind, task_id, trace_id, actor, action, target, thread, summary, payload_json. |
| `task_index` | Denormalized task fields from `map.db`/task JSON: status, owner, claimed_by, attempts, output_paths_json, criteria_json. |
| `agent_index` | Agent IDs observed in MAP/hcom/liveness with current state and last_seen_at. |
| `links` | Typed edges between replay rows, tasks, agents, artifacts, hcom event IDs, transcript references, and review records. |
| `drift_findings` | Rebuild-time source disagreement, parse failures, missing task refs, or stale mirrors. |

Do not store full transcript bodies in the first implementation. Store pointers:

```text
hcom transcript <agent> <range> --full
hcom events --sql 'id BETWEEN X AND Y'
```

This keeps the index useful without duplicating private conversation text into
another persistent database before retention rules are defined.

## Normalized Event Shape

Every derived event should expose a small common shape:

```json
{
  "replay_id": "map-events:920",
  "source": "map_events_jsonl",
  "source_event_id": "920",
  "created_at": "2026-07-14T03:51:50Z",
  "kind": "PROGRESS",
  "task_id": "TASK-172",
  "trace_id": "task:TASK-172",
  "actor": "codex-lab-mozu",
  "action": "progress",
  "target": "TASK-172",
  "thread": null,
  "summary": "Created TASK-172: Design MAP session replay read model (READY)"
}
```

Hcom event rows should preserve hcom IDs:

```json
{
  "replay_id": "hcom:31942",
  "source": "hcom_events",
  "source_event_id": "31942",
  "kind": "message",
  "actor": "claude-lab-zera",
  "action": "inform",
  "target": "codex-lab-mozu",
  "thread": null,
  "summary": "TASK-171 APPROVED..."
}
```

When hcom events mention a task ID in message text, command detail, or status
detail, link them to that task with link type `mentions_task`. Do not infer
ownership transfer from a mention.

## Query Surfaces

The first implementation should expose a small Python API and CLI before adding
new UI behavior.

Recommended CLI:

```bash
python3 MAP_System/scripts/session_replay.py build
python3 MAP_System/scripts/session_replay.py status
python3 MAP_System/scripts/session_replay.py task TASK-171 --limit 50
python3 MAP_System/scripts/session_replay.py agent codex-lab-mozu --limit 50
python3 MAP_System/scripts/session_replay.py trace task:TASK-171
python3 MAP_System/scripts/session_replay.py hcom 31942
```

Recommended mission-control integration:

- Replace `get_task_drilldown()`'s recent-events-only view with a replay query
  when the replay index exists.
- Keep the current `events.jsonl` fallback when the index is missing or stale.
- Add a visible "replay stale" warning through the existing attention/drift
  pattern rather than silently showing old data.
- Add no write-capable controls.

Recommended Command Center use:

- Read the same CLI/API output.
- Prefer task/trace/agent filters over transcript dumps.
- Keep hcom transcript references clickable/copyable for the operator, but
  avoid bulk transcript duplication in MAP artifacts.

## Drift Checks

The build command should fail or warn loudly on:

- `validate_task_mirrors.py` failure.
- `events.jsonl` parse errors.
- MAP events with task IDs missing from `map.db`/`tasks/`.
- Task JSON output paths that do not exist when the task is approved or
  submitted, unless the path is explicitly external.
- Duplicate hcom event IDs in the derived store.
- Hcom command/status rows that mention file writes under another active
  task's output paths within a collision window.
- Source high-water mark moving backward without an explicit rebuild.

The status command should report:

- indexed source high-water marks;
- last build time;
- row counts by source/kind;
- drift finding count;
- whether the replay index is safe for mission-control to use.

## Privacy And Scope Boundaries

- Local-only. No network service, web dashboard, or background daemon in the
  first implementation.
- No direct dependency on `repo/agents-observe-main` code.
- No transcript bulk import by default.
- No writes to `map.db`, task JSON, `events.jsonl`, hcom storage, or workflow
  files from mission-control replay views.
- No hidden helper work. If a helper is later used to inspect replay findings,
  it must be visible and task-scoped per `MAP_System/AGENTS.md`.
- No external CommandCenterUI changes unless a separate approved task names
  `/home/home/Projects/CommandCenterUI` as an output path and provides restart
  and validation steps.

## Implementation Tasks

Recommended next sequence:

1. `TASK-173` candidate: implement `session_replay.py build/status/task/agent/trace`
   against `events.jsonl`, task JSON, and `map.db` only. Do not ingest hcom yet.
2. `TASK-174` candidate: add hcom event ingestion through `hcom events --all`
   or bounded `--after` windows, preserving source IDs and transcript pointers.
3. `TASK-175` candidate: integrate mission-control read-only drilldowns with
   replay fallback and stale-index warnings.
4. Deferred: direct hcom DB adapter, transcript body indexing, external UI
   integration, or write-control coupling.

## Acceptance Mapping

- Canonical input sources, derived indexes, and drift checks are defined above
  without changing source authority.
- Read-only query surfaces are defined for task, trace, agent, session/hcom,
  and mission-control drilldowns.
- Privacy/scope boundaries explicitly reject external code adoption, services,
  transcript duplication, and write authority.
- Concrete implementation tasks are recommended, with hcom ingestion and UI
  integration separated behind the minimal MAP-only replay builder.
