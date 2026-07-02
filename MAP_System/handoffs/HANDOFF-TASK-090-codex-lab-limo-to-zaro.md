# HANDOFF TASK-090 codex-lab-limo to claude-lab-zaro

Task ID: TASK-090
Sender: codex-lab-limo
Intended recipient: claude-lab-zaro
Status: WAITING_OPERATOR_DECISION
Created: 2026-07-02 13:40 EDT

## Completed

- Claimed TASK-090 through `MAP_System.db.claims.claim_task_with_reason`.
- Set `claude-lab-rose` to `inactive` / `session_superseded` in SQLite.
- Added `scratch-peso` to SQLite as `inactive` / `disposable_session_ended`.
- Exported mirrors through `MAP_System/migration/export_to_files.py`.
- Preserved `scratch-peso` in `MAP_System/agents/status.json` with an explicit
  note that it was a disposable TASK-089 test agent.
- Cleared the `scratch-peso` incident from
  `MAP_System/agents/limit-watcher-state.json` while the real watcher process
  was stopped.
- Stopped obsolete watcher PID `326341` from the old Downloads path.
- Started the current Projects watcher in a bounded tmux daemon session:
  `map-limit-watcher`, PID `439403`.
- Filed emergence idea:
  `MAP_System/emergence/ideas/IDEA-0009-rns-should-ignore-superseded-and-disposable-sessions.md`.
- Rebuilt `MAP_System/emergence/INDEX.md`.
- Recorded a TASK-090 progress event in `MAP_System/events/events.jsonl`.

## Verification

- `python3 MAP_System/scripts/validate_task_graph.py`: passed.
- `python3 MAP_System/scripts/validate_events.py`: errors=0, warnings=33.
- `python3 MAP_System/scripts/map_emergence.py validate`: 23 checked.
- `python3 MAP_System/scripts/map_emergence.py stale`: no findings.
- `python3 MAP_System/scripts/limit_watcher.py --once --dry-run`: no output,
  meaning no dry-run nudges/incidents.
- `tmux ls`: `map-limit-watcher` session present.
- `ps -fp $(cat MAP_System/.locks/limit-watcher.pid)`: PID `439403` running
  `python3 -u MAP_System/scripts/limit_watcher.py --interval 60`.

## Remaining Blocker

`MAP_System/shared/canonical-repo.md` is intentionally unchanged. Zaro sent
the operator confirmation request as hcom #16913, but no `bigboss` confirmation
was visible to limo before this handoff.

Required next step after confirmation:

- If `bigboss` confirms `/home/home/Projects/MultiAgentProject` as canonical,
  refresh `MAP_System/shared/canonical-repo.md` and HPOM headers.
- If `bigboss` chooses different wording, follow that direction.

Do not edit `canonical-repo.md` without that explicit operator confirmation.

## Known Limitations

- Starting the watcher through `MAP_System/scripts/start-limit-watcher.sh` from
  the Codex tool execution surface verified briefly but the child process was
  culled after command completion. The durable runtime used here is a dedicated
  tmux session, not a hidden agent/helper.
- The latest normal lab launcher should still start the watcher on lab open.
  This tmux session is a maintenance backstop for TASK-090.
