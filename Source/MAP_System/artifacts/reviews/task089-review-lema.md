# Review Record: TASK-089

## Header

```text
task_id:      TASK-089
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
| 1 | Opening the app with lab down brings the lab up; lab state visible | PASS | `window.py` calls `ensure_lab()` after server start; `ensure_lab()` uses fixed `/api/lab/status` then same-origin `/api/lab/start`. `server.py` uses fixed `~/.local/bin/ai-command-center-lab` with no client-provided arguments. Live `/api/lab/status` returned lab agents and launcher availability; same-origin `/api/lab/start` with agents alive returned `already_running: true` without starting another lab. |
| 2 | Clicking an agent opens a live terminal screen in-app | PASS | `chat.js` adds a per-agent `view` button and polls `/api/term?name=...`; live `GET /api/term?name=lema` returned screen JSON with terminal rows. Invalid names returned 400. |
| 3 | Operator can inject text/Enter with same-origin, validated name, capped text | PASS | `POST /api/term/inject` validates name through the hcom instances table, caps text at 500 chars, rejects empty no-op, and uses argv-list `hcom term inject`. Live malformed tests returned 400/403 as expected. Claude validated a disposable visible scratch-agent injection end to end. |
| 4 | hcom term reads are read-only; inject only fires on explicit operator action | PASS | Term reads call `hcom term <name> --json`; hcom DB connection uses SQLite `mode=ro` and a write probe failed with readonly database. UI inject is wired only to the screen panel submit and Enter-only button. |

## Files Reviewed

- `/home/home/Projects/CommandCenterUI/app/server.py`
- `/home/home/Projects/CommandCenterUI/app/window.py`
- `/home/home/Projects/CommandCenterUI/src/chat.html`
- `/home/home/Projects/CommandCenterUI/src/chat.js`
- `/home/home/Projects/CommandCenterUI/src/chat.css`
- `/home/home/Projects/CommandCenterUI/README.md`
- `/home/home/Projects/CommandCenterUI/artifacts/task089-validation.md`
- `MAP_System/tasks/TASK-089.json`

## Forbidden Changes

- No headless agents or hidden helper launches added; lab start uses the existing visible wezterm lab launcher.
- No raw hcom DB writes.
- No client-controlled process arguments for lab start.
- No injection into arbitrary names; target must be a live hcom instance.

## Security Second Pass

Scope: TASK-089 adds lab lifecycle control and a write-capable terminal injection endpoint.

- Authentication/authority: this is a local operator UI. Inject is same-origin guarded and requires explicit UI action.
- CSRF/drive-by exposure: cross-origin `/api/term/inject` and `/api/lab/start` POSTs returned HTTP 403.
- Injection: subprocess calls use argv lists, not shell strings. Lab start uses a fixed launcher path. Terminal injection accepts only validated instance names and bounded text.
- Target validation: `known_instance()` checks strict `HCOM_NAME_RE` first, then requires the name to exist in the hcom `instances` table.
- Read-only surfaces: hcom message/presence and term reads do not write to hcom DB; the SQLite connection uses `mode=ro`.
- Auditability: terminal injections append JSONL records under `runtime/inject-audit.jsonl` with operator, target, text, enter flag, and return code.
- Failure modes: invalid agent names, path-like names, empty no-op, oversized text, and malformed/cross-origin requests fail without injection.

Residual risk: same-origin protection still permits local no-Origin/no-Referer processes, as documented since TASK-060. That remains a localhost/local-process risk; local processes can already run `hcom term inject` directly under the same user account. Not blocking.

## Verification

```bash
python3 MAP_System/migration/export_to_files.py --db MAP_System/map.db
python3 - <<'PY'
from pathlib import Path
for path in ['/home/home/Projects/CommandCenterUI/app/server.py','/home/home/Projects/CommandCenterUI/app/window.py']:
    compile(Path(path).read_text(), path, 'exec')
PY
bash -n /home/home/Projects/CommandCenterUI/run-command-center-app.sh /home/home/Projects/CommandCenterUI/launch-command-center-ui.sh
python3 MAP_System/scripts/validate_task_graph.py
python3 MAP_System/scripts/validate_events.py
python3 MAP_System/scripts/validate_shared_state.py
```

Live endpoint checks:

- `GET /api/lab/status`
- `POST /api/lab/start`
- `GET /api/term?name=lema`
- malformed `/api/term` and `/api/term/inject` requests
- hcom DB readonly write probe
