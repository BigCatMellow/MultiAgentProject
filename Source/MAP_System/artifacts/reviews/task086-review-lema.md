# Review Record: TASK-086

## Header

```text
task_id:      TASK-086
reviewer:     codex-lab-lema
review_date:  2026-07-02
task_owner:   claude-lab-zaro
```

Reviewer != owner. Independence check passes.

## Verdict

```text
APPROVED
```

## Acceptance Criteria

| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | `server.py` resolves the MAP workspace regardless of where CommandCenterUI lives | PASS | Discovery mode resolves `WORKSPACE` to `/home/home/Projects/MultiAgentProject`; valid `COMMAND_CENTER_UI_WORKSPACE=/home/home/Projects/MultiAgentProject` resolves correctly on import; bad override `/nonexistent` exits loudly instead of falling back. |
| 2 | `GET /api/snapshot` returns non-empty live events/tasks/agents_status | PASS | Live server on `127.0.0.1:8876` returned `ok=True`, workspace `/home/home/Projects/MultiAgentProject`, 5 events, `tasks_total=76`, counts including `SUBMITTED=1`, and 19 agents. |
| 3 | `CommandCenterUI.desktop` Exec path matches the real current location | PASS | Desktop file now uses `/home/home/Projects/CommandCenterUI/run-command-center-app.sh`; `desktop-file-validate` exits 0 with only the pre-existing multi-category hint. |
| 4 | README reflects the standalone layout accurately | PASS | README run path now points at `/home/home/Projects/CommandCenterUI/run-command-center-app.sh` and documents standalone layout plus workspace discovery/override behavior. |

## Files Reviewed

- `/home/home/Projects/CommandCenterUI/app/server.py`
- `/home/home/Projects/CommandCenterUI/CommandCenterUI.desktop`
- `/home/home/Projects/CommandCenterUI/README.md`
- `/home/home/Projects/CommandCenterUI/artifacts/task086-validation.md`
- `MAP_System/tasks/TASK-086.json`
- `MAP_System/workflow/task_graph.json`

## Forbidden Changes

- No changes to the existing hcom send command construction or sender-identity model beyond workspace path resolution.
- No LAN exposure; reviewed default launcher/server binding remains `127.0.0.1`.
- No hidden/headless helper process added.
- No publication or install outside the standalone project path.

## Security Second Pass

Scope: `app/server.py` is a localhost server with a write-capable `/api/hcom/send` endpoint when launched with a registered hcom identity.

- Binding remains localhost-only by default (`127.0.0.1` launcher default).
- Default `browser` identity still blocks hcom sends with HTTP 403; same-origin POST in browser mode returned the expected identity error, not a send.
- Cross-origin POST with `Origin: http://evil.example` returned HTTP 403 before payload handling.
- Malformed `limit` values on `/api/snapshot` and `/api/events` return HTTP 400.
- Workspace override fails closed when explicitly invalid, avoiding silent reads from the wrong directory.

Residual risk: requests with both `Origin` and `Referer` absent are still allowed through the origin gate, as previously documented in TASK-060. That does not increase browser CSRF risk and is unchanged by TASK-086; hcom sends still require explicit non-browser identity.

## Verification Commands

```bash
python3 /home/home/Projects/CommandCenterUI/app/server.py --host 127.0.0.1 --port 8876
python3 -c "import json, urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8876/api/snapshot?limit=5')); print(data['workspace'], data['tasks']['total'])"
COMMAND_CENTER_UI_WORKSPACE=/nonexistent python3 /home/home/Projects/CommandCenterUI/app/server.py --host 127.0.0.1 --port 8877
bash -n /home/home/Projects/CommandCenterUI/run-command-center-app.sh /home/home/Projects/CommandCenterUI/launch-command-center-ui.sh
desktop-file-validate /home/home/Projects/CommandCenterUI/CommandCenterUI.desktop
python3 MAP_System/scripts/validate_task_graph.py
python3 MAP_System/scripts/validate_events.py
python3 MAP_System/scripts/validate_shared_state.py
```
